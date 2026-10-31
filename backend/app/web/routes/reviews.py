"""FastAPI route handlers for review ingestion, listing, detail, mentor triage, and export."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.adapters.db.models import DecisionRecord, FindingRecord, ReviewRecord
from app.adapters.db.repository import ReviewRepository
from app.domain.exceptions import EntityNotFoundError
from app.schemas.api import (
    DecisionRequest,
    DecisionResponse,
    FindingResponse,
    ReviewCreateRequest,
    ReviewListItemResponse,
    ReviewResponse,
)
from app.services.review_service import ReviewService
from app.web.auth import verify_mentor_token
from app.web.dependencies import get_db, get_review_service

router = APIRouter(prefix="/api/v1", tags=["Reviews & Mentor Triage"])


def _to_decision_response(d: DecisionRecord | None) -> DecisionResponse | None:
    if not d:
        return None
    return DecisionResponse(
        id=d.id,
        finding_id=d.finding_id,
        action=d.action,
        original_quote=d.original_quote,
        original_explanation=d.original_explanation,
        original_suggested_fix=d.original_suggested_fix,
        original_severity=d.original_severity,
        edited_quote=d.edited_quote,
        edited_explanation=d.edited_explanation,
        edited_suggested_fix=d.edited_suggested_fix,
        edited_severity=d.edited_severity,
        mentor_notes=d.mentor_notes,
        mentor_id=d.mentor_id,
        decided_at=d.decided_at,
    )


def _to_finding_response(f: FindingRecord) -> FindingResponse:
    return FindingResponse(
        id=f.id,
        review_id=f.review_id,
        rule_id=f.rule_id,
        severity=f.severity,
        file=f.file,
        line_start=f.line_start,
        line_end=f.line_end,
        evidence_quote=f.evidence_quote,
        explanation=f.explanation,
        suggested_fix=f.suggested_fix,
        confidence=f.confidence,
        created_at=f.created_at,
        decision=_to_decision_response(f.decision),
    )


def _to_review_response(r: ReviewRecord) -> ReviewResponse:
    return ReviewResponse(
        id=r.id,
        repo_full_name=r.repo_full_name,
        pr_number=r.pr_number,
        pr_title=r.pr_title,
        pr_description=r.pr_description,
        author_username=r.author_username,
        base_commit_sha=r.base_commit_sha,
        head_commit_sha=r.head_commit_sha,
        status=r.status,
        summary=r.summary,
        raw_diff=r.raw_diff or "",
        is_truncated=r.is_truncated,
        provider=r.provider,
        model=r.model,
        latency_ms=r.latency_ms,
        tokens=r.tokens,
        est_cost=r.est_cost,
        created_at=r.created_at,
        updated_at=r.updated_at,
        findings=[_to_finding_response(f) for f in r.findings],
    )


@router.post(
    "/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_review",
    summary="Trigger code review for a GitHub PR",
)
async def create_review(
    payload: ReviewCreateRequest,
    session: Annotated[Session, Depends(get_db)],
    review_service: Annotated[ReviewService, Depends(get_review_service)],
) -> ReviewResponse:
    """Ingest, analyze, verify evidence, and persist an AI review for the given pull request."""
    review_record = await review_service.review_pull_request(
        pr_url=payload.pr_url,
        session=session,
    )
    return _to_review_response(review_record)


@router.get(
    "/reviews",
    response_model=list[ReviewListItemResponse],
    operation_id="list_reviews",
    summary="List code reviews with optional status filter",
)
def list_reviews(
    session: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Page limit")] = 50,
    status: Annotated[str | None, Query(description="Filter by review status (e.g. PENDING_APPROVAL, APPROVED)")] = None,
) -> list[ReviewListItemResponse]:
    """Retrieve a list of past pull request reviews."""
    repo = ReviewRepository(session)
    reviews = repo.list_reviews(skip=skip, limit=limit, status=status)

    items: list[ReviewListItemResponse] = []
    for r in reviews:
        findings_count = len(r.findings)
        approved_count = sum(
            1 for f in r.findings if f.decision and f.decision.action in ("APPROVE", "EDIT")
        )
        items.append(
            ReviewListItemResponse(
                id=r.id,
                repo_full_name=r.repo_full_name,
                pr_number=r.pr_number,
                pr_title=r.pr_title,
                author_username=r.author_username,
                status=r.status,
                provider=r.provider,
                model=r.model,
                findings_count=findings_count,
                approved_count=approved_count,
                created_at=r.created_at,
            )
        )
    return items


@router.get(
    "/reviews/{id}",
    response_model=ReviewResponse,
    operation_id="get_review",
    summary="Retrieve detailed review session by ID",
)
def get_review(
    id: str,
    session: Annotated[Session, Depends(get_db)],
) -> ReviewResponse:
    """Fetch complete review details, including all generated findings and mentor decisions."""
    repo = ReviewRepository(session)
    review = repo.get_review(id)
    if not review:
        raise EntityNotFoundError(f"Review with id '{id}' not found.")
    return _to_review_response(review)


@router.post(
    "/findings/{id}/decision",
    response_model=DecisionResponse,
    operation_id="record_finding_decision",
    summary="Submit mentor triage decision for a finding",
)
def record_finding_decision(
    id: str,
    payload: DecisionRequest,
    session: Annotated[Session, Depends(get_db)],
    _mentor_token: Annotated[str, Depends(verify_mentor_token)],
) -> DecisionResponse:
    """Mentor approves, edits, or rejects an AI finding. Updates review aggregate status."""
    repo = ReviewRepository(session)
    decision = repo.record_decision(
        finding_id=id,
        action=payload.action,
        mentor_notes=payload.mentor_notes,
        edited_quote=payload.edited_quote,
        edited_explanation=payload.edited_explanation,
        edited_suggested_fix=payload.edited_suggested_fix,
        edited_severity=payload.edited_severity,
    )
    res = _to_decision_response(decision)
    assert res is not None
    return res


@router.get(
    "/reviews/{id}/export",
    operation_id="export_review_comments",
    summary="Export approved comments as Markdown",
    response_class=Response,
    responses={
        200: {
            "content": {"text/markdown": {}},
            "description": "Rendered Markdown containing exclusively mentor-approved review comments.",
        }
    },
)
def export_review_comments(
    id: str,
    session: Annotated[Session, Depends(get_db)],
    _mentor_token: Annotated[str, Depends(verify_mentor_token)],
) -> Response:
    """Export approved comments only (omitting pending and rejected comments) as formatted Markdown."""
    repo = ReviewRepository(session)
    review = repo.get_review(id)
    if not review:
        raise EntityNotFoundError(f"Review with id '{id}' not found.")

    # Filter strictly to findings with human mentor APPROVE or EDIT
    approved_findings = [
        f for f in review.findings
        if f.decision and f.decision.action in ("APPROVE", "EDIT")
    ]

    lines: list[str] = [
        f"# BitElevate PR Review: {review.repo_full_name}#{review.pr_number}",
        "",
        f"- **Title:** {review.pr_title}",
        f"- **Author:** @{review.author_username}",
        f"- **Review Status:** {review.status}",
        f"- **Attribution:** {review.provider} ({review.model})",
        "",
        "## Summary",
        review.summary or "No summary provided.",
        "",
        f"## Approved Comments ({len(approved_findings)})",
        "",
    ]

    if not approved_findings:
        lines.append("*No approved mentor comments for this pull request.*")
    else:
        for idx, finding in enumerate(approved_findings, start=1):
            decision = finding.decision
            assert decision is not None

            quote = decision.edited_quote or decision.original_quote
            explanation = decision.edited_explanation or decision.original_explanation
            suggested_fix = decision.edited_suggested_fix or decision.original_suggested_fix
            severity = (decision.edited_severity or decision.original_severity).upper()

            lines.append(f"### {idx}. [{severity}] `{finding.file}` (Lines {finding.line_start}-{finding.line_end})")
            lines.append(f"**Rule:** `{finding.rule_id}`")
            lines.append("")
            lines.append("> " + quote.replace("\n", "\n> "))
            lines.append("")
            lines.append(f"**Explanation:** {explanation}")
            lines.append("")
            lines.append("```suggestion")
            lines.append(suggested_fix)
            lines.append("```")
            if decision.mentor_notes:
                lines.append("")
                lines.append(f"**Mentor Note:** *{decision.mentor_notes}*")
            lines.append("")
            lines.append("---")
            lines.append("")

    markdown_text = "\n".join(lines)
    return Response(content=markdown_text, media_type="text/markdown; charset=utf-8")
