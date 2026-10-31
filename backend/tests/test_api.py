"""Comprehensive integration tests for FastAPI review routes, mentor auth, and error handling."""
import json
from collections.abc import Generator

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.db.session import DatabaseManager, get_db_manager
from app.adapters.github_client import GitHubClient
from app.adapters.llm_client import MockLLMClient
from app.config import Settings, get_settings
from app.services.ingestion import IngestionService
from app.services.review_service import ReviewService
from app.services.sanitizer import InputSanitizerService
from app.web.dependencies import get_db, get_review_service
from app.web.main import create_app
from tests.fixtures.recorded_github_pr import RECORDED_DIFF_42, RECORDED_METADATA_42


@pytest.fixture
def test_settings() -> Settings:
    """Settings configured for testing with in-memory SQLite and test mentor token."""
    return Settings(
        APP_ENV="testing",
        DATABASE_URL="sqlite:///:memory:",
        MENTOR_TOKEN="test-mentor-token-xyz",
        LLM_PROVIDER="mock",
    )


@pytest.fixture
def test_db_manager(test_settings: Settings) -> DatabaseManager:
    """DatabaseManager connected to in-memory SQLite with schema pre-created."""
    manager = DatabaseManager(test_settings)
    manager.create_tables()
    return manager


@pytest.fixture
def mock_review_service(test_settings: Settings) -> ReviewService:
    """ReviewService utilizing MockTransport for deterministic PR fetching."""
    def mock_github_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if url_str.endswith("/pulls/42"):
            if "application/vnd.github.v3.diff" in request.headers.get("Accept", ""):
                return httpx.Response(200, text=RECORDED_DIFF_42)
            return httpx.Response(200, text=json.dumps(RECORDED_METADATA_42))
        return httpx.Response(404, text=json.dumps({"message": "Not Found"}))

    transport = httpx.MockTransport(mock_github_handler)
    gh_http_client = httpx.AsyncClient(transport=transport)
    gh_client = GitHubClient(http_client=gh_http_client)
    ingestion = IngestionService(github_client=gh_client)
    sanitizer = InputSanitizerService()
    llm = MockLLMClient()

    return ReviewService(
        settings=test_settings,
        ingestion_service=ingestion,
        sanitizer_service=sanitizer,
        llm_client=llm,
    )


@pytest.fixture
def api_client(
    test_settings: Settings,
    test_db_manager: DatabaseManager,
    mock_review_service: ReviewService,
) -> Generator[TestClient, None, None]:
    """TestClient wired with in-memory database and deterministic review service."""
    app = create_app(test_settings)

    def override_get_settings() -> Settings:
        return test_settings

    def override_get_db() -> Generator[Session, None, None]:
        session = test_db_manager.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def override_get_review_service() -> ReviewService:
        return mock_review_service

    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_review_service] = override_get_review_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    test_db_manager.drop_tables()


def test_health_check_and_request_id_middleware(api_client: TestClient) -> None:
    """Verify /health returns 200 and RequestIDMiddleware injects correlation ID."""
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app_env": "testing"}
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 10

    # Custom request ID propagation
    custom_id = "test-req-correlation-1234"
    resp_custom = api_client.get("/health", headers={"X-Request-ID": custom_id})
    assert resp_custom.headers["X-Request-ID"] == custom_id


def test_create_review_success(api_client: TestClient) -> None:
    """Verify POST /api/v1/reviews triggers pipeline and returns ReviewResponse."""
    payload = {"pr_url": "https://github.com/cynbit/bitelevate-sample/pull/42"}
    response = api_client.post("/api/v1/reviews", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["repo_full_name"] == "cynbit/bitelevate-sample"
    assert data["pr_number"] == 42
    assert data["status"] == "PENDING_APPROVAL"
    assert data["provider"] == "mock"
    assert len(data["findings"]) >= 1

    first_finding = data["findings"][0]
    assert first_finding["review_id"] == data["id"]
    assert first_finding["evidence_quote"] != ""
    assert first_finding["decision"] is None


def test_create_review_invalid_url_returns_safe_error(api_client: TestClient) -> None:
    """Verify invalid PR URL produces safe error payload with error_id."""
    payload = {"pr_url": "https://gitlab.com/unsupported/repo/pull/1"}
    response = api_client.post("/api/v1/reviews", json=payload)
    assert response.status_code == 400

    data = response.json()
    assert "error_id" in data
    assert "Only 'github.com' is supported" in data["message"]
    # Ensure no internal stack trace or file path leaked
    assert "Traceback" not in response.text
    assert "D:\\" not in response.text


def test_list_and_get_review(api_client: TestClient) -> None:
    """Verify listing and detail retrieval of reviews."""
    # Create review first
    create_resp = api_client.post(
        "/api/v1/reviews",
        json={"pr_url": "https://github.com/cynbit/bitelevate-sample/pull/42"},
    )
    assert create_resp.status_code == 201
    review_id = create_resp.json()["id"]

    # List reviews
    list_resp = api_client.get("/api/v1/reviews")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["id"] == review_id
    assert items[0]["findings_count"] >= 1
    assert items[0]["approved_count"] == 0

    # Get review detail
    detail_resp = api_client.get(f"/api/v1/reviews/{review_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == review_id

    # Get non-existent review
    not_found_resp = api_client.get("/api/v1/reviews/missing-uuid-404")
    assert not_found_resp.status_code == 404
    assert "error_id" in not_found_resp.json()


def test_mentor_auth_validation_on_decision(api_client: TestClient) -> None:
    """Verify mentor authentication is strictly enforced with constant-time check."""
    create_resp = api_client.post(
        "/api/v1/reviews",
        json={"pr_url": "https://github.com/cynbit/bitelevate-sample/pull/42"},
    )
    finding_id = create_resp.json()["findings"][0]["id"]

    # 1. Missing token
    resp_no_auth = api_client.post(
        f"/api/v1/findings/{finding_id}/decision",
        json={"action": "APPROVE"},
    )
    assert resp_no_auth.status_code == 401

    # 2. Invalid token
    resp_bad_auth = api_client.post(
        f"/api/v1/findings/{finding_id}/decision",
        headers={"X-Mentor-Token": "wrong-token-abc"},
        json={"action": "APPROVE"},
    )
    assert resp_bad_auth.status_code == 401

    # 3. Valid token via header
    resp_valid = api_client.post(
        f"/api/v1/findings/{finding_id}/decision",
        headers={"X-Mentor-Token": "test-mentor-token-xyz"},
        json={"action": "APPROVE", "mentor_notes": "Well spotted"},
    )
    assert resp_valid.status_code == 200
    decision_data = resp_valid.json()
    assert decision_data["action"] == "APPROVE"
    assert decision_data["original_quote"] != ""


def test_mentor_decision_edit_keeps_original_and_edited_text(api_client: TestClient) -> None:
    """Verify EDIT decision stores both original finding fields and mentor overrides."""
    create_resp = api_client.post(
        "/api/v1/reviews",
        json={"pr_url": "https://github.com/cynbit/bitelevate-sample/pull/42"},
    )
    finding = create_resp.json()["findings"][0]
    finding_id = finding["id"]

    edit_payload = {
        "action": "EDIT",
        "mentor_notes": "Clarified explanation for intern",
        "edited_explanation": "Intern: Please index the foreign key to avoid sequential scans.",
        "edited_suggested_fix": "CREATE INDEX idx_user_id ON orders(user_id);",
        "edited_severity": "blocker",
    }

    resp = api_client.post(
        f"/api/v1/findings/{finding_id}/decision",
        headers={"Authorization": "Bearer test-mentor-token-xyz"},
        json=edit_payload,
    )
    assert resp.status_code == 200
    d = resp.json()

    # Original fields preserved
    assert d["original_explanation"] == finding["explanation"]
    assert d["original_suggested_fix"] == finding["suggested_fix"]
    assert d["original_severity"] == finding["severity"]

    # Edited fields present
    assert d["edited_explanation"] == edit_payload["edited_explanation"]
    assert d["edited_suggested_fix"] == edit_payload["edited_suggested_fix"]
    assert d["edited_severity"] == "blocker"
    assert d["mentor_notes"] == edit_payload["mentor_notes"]


def test_export_markdown_approved_comments_only(api_client: TestClient) -> None:
    """Verify Markdown export contains exclusively approved/edited comments and excludes rejected ones."""
    create_resp = api_client.post(
        "/api/v1/reviews",
        json={"pr_url": "https://github.com/cynbit/bitelevate-sample/pull/42"},
    )
    review_id = create_resp.json()["id"]
    findings = create_resp.json()["findings"]
    assert len(findings) >= 2

    # Finding 1: APPROVE
    api_client.post(
        f"/api/v1/findings/{findings[0]['id']}/decision",
        headers={"X-Mentor-Token": "test-mentor-token-xyz"},
        json={"action": "APPROVE", "mentor_notes": "Great catch on security"},
    )

    # Finding 2: REJECT
    api_client.post(
        f"/api/v1/findings/{findings[1]['id']}/decision",
        headers={"X-Mentor-Token": "test-mentor-token-xyz"},
        json={"action": "REJECT", "mentor_notes": "False positive in test harness"},
    )

    # Export without auth -> 401
    resp_unauth = api_client.get(f"/api/v1/reviews/{review_id}/export")
    assert resp_unauth.status_code == 401

    # Export with auth -> 200 text/markdown
    resp_export = api_client.get(
        f"/api/v1/reviews/{review_id}/export",
        headers={"X-Mentor-Token": "test-mentor-token-xyz"},
    )
    assert resp_export.status_code == 200
    assert "text/markdown" in resp_export.headers["content-type"]

    md_text = resp_export.text
    # Approved finding must be in markdown
    assert findings[0]["rule_id"] in md_text
    assert "Great catch on security" in md_text

    # Rejected finding rule must NOT be in markdown
    assert findings[1]["rule_id"] not in md_text
    assert "False positive in test harness" not in md_text


def test_export_markdown_when_zero_comments_approved(api_client: TestClient) -> None:
    """Verify friendly fallback message when no comments are approved."""
    create_resp = api_client.post(
        "/api/v1/reviews",
        json={"pr_url": "https://github.com/cynbit/bitelevate-sample/pull/42"},
    )
    review_id = create_resp.json()["id"]

    resp = api_client.get(
        f"/api/v1/reviews/{review_id}/export",
        headers={"X-Mentor-Token": "test-mentor-token-xyz"},
    )
    assert resp.status_code == 200
    assert "*No approved mentor comments for this pull request.*" in resp.text
