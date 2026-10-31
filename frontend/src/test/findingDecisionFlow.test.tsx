import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { FindingCard } from "../components/FindingCard";
import { FindingEditModal } from "../components/FindingEditModal";
import { IngestBar } from "../components/IngestBar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import type { FindingResponse } from "../api/client";

const mockFinding: FindingResponse = {
  id: "finding-123",
  review_id: "review-456",
  rule_id: "SEC_JWT_UNVERIFIED",
  severity: "critical",
  file: "app/auth.py",
  line_start: 42,
  line_end: 45,
  evidence_quote: "jwt.decode(token, verify=False)",
  explanation: "JWT decoded without cryptographic signature verification allows forgery.",
  suggested_fix: "jwt.decode(token, key=SECRET, algorithms=['HS256'])",
  confidence: 0.98,
  created_at: "2026-10-31T10:00:00Z",
  decision: null,
};

describe("Finding Decision Triage Flow", () => {
  it("renders finding details with unapproved pending state", () => {
    const onApprove = vi.fn();
    const onEdit = vi.fn();
    const onReject = vi.fn();
    const onSelect = vi.fn();

    render(
      <FindingCard
        finding={mockFinding}
        index={0}
        isSelected={false}
        onSelect={onSelect}
        onApprove={onApprove}
        onEdit={onEdit}
        onReject={onReject}
      />
    );

    expect(screen.getByText("SEC_JWT_UNVERIFIED")).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText("Pending Mentor Triage")).toBeInTheDocument();
    expect(screen.getByText("jwt.decode(token, verify=False)")).toBeInTheDocument();
  });

  it("triggers approve callback when Approve button is clicked", () => {
    const onApprove = vi.fn();
    const onEdit = vi.fn();
    const onReject = vi.fn();
    const onSelect = vi.fn();

    render(
      <FindingCard
        finding={mockFinding}
        index={0}
        isSelected={false}
        onSelect={onSelect}
        onApprove={onApprove}
        onEdit={onEdit}
        onReject={onReject}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /approve finding 1/i });
    fireEvent.click(approveBtn);

    expect(onApprove).toHaveBeenCalledTimes(1);
    expect(onReject).not.toHaveBeenCalled();
    expect(onEdit).not.toHaveBeenCalled();
  });

  it("triggers reject callback when Reject button is clicked", () => {
    const onApprove = vi.fn();
    const onEdit = vi.fn();
    const onReject = vi.fn();
    const onSelect = vi.fn();

    render(
      <FindingCard
        finding={mockFinding}
        index={0}
        isSelected={false}
        onSelect={onSelect}
        onApprove={onApprove}
        onEdit={onEdit}
        onReject={onReject}
      />
    );

    const rejectBtn = screen.getByRole("button", { name: /reject finding 1/i });
    fireEvent.click(rejectBtn);

    expect(onReject).toHaveBeenCalledTimes(1);
    expect(onApprove).not.toHaveBeenCalled();
  });

  it("displays approved status badge when finding is approved", () => {
    const approvedFinding: FindingResponse = {
      ...mockFinding,
      decision: {
        id: "dec-1",
        finding_id: mockFinding.id,
        action: "APPROVE",
        original_quote: mockFinding.evidence_quote,
        original_explanation: mockFinding.explanation,
        original_suggested_fix: mockFinding.suggested_fix,
        original_severity: mockFinding.severity,
        edited_quote: null,
        edited_explanation: null,
        edited_suggested_fix: null,
        edited_severity: null,
        mentor_notes: null,
        mentor_id: "mentor-1",
        decided_at: "2026-10-31T10:05:00Z",
      },
    };

    render(
      <FindingCard
        finding={approvedFinding}
        index={0}
        isSelected={false}
        onSelect={vi.fn()}
        onApprove={vi.fn()}
        onEdit={vi.fn()}
        onReject={vi.fn()}
      />
    );

    expect(screen.getByText(/Approved/i)).toBeInTheDocument();
  });

  it("displays edited content and preserves original text next to it", () => {
    const editedFinding: FindingResponse = {
      ...mockFinding,
      decision: {
        id: "dec-2",
        finding_id: mockFinding.id,
        action: "EDIT",
        original_quote: mockFinding.evidence_quote,
        original_explanation: mockFinding.explanation,
        original_suggested_fix: mockFinding.suggested_fix,
        original_severity: mockFinding.severity,
        edited_quote: "jwt.decode(token, verify=False)  # edited quote",
        edited_explanation: "Mentor updated explanation: verify token signature with key.",
        edited_suggested_fix: "jwt.decode(token, key=SECRET)",
        edited_severity: "critical",
        mentor_notes: "Follow up with intern during weekly 1:1",
        mentor_id: "mentor-1",
        decided_at: "2026-10-31T10:10:00Z",
      },
    };

    render(
      <FindingCard
        finding={editedFinding}
        index={0}
        isSelected={false}
        onSelect={vi.fn()}
        onApprove={vi.fn()}
        onEdit={vi.fn()}
        onReject={vi.fn()}
      />
    );

    expect(screen.getByText(/Edited & Approved/i)).toBeInTheDocument();
    expect(screen.getByText("Mentor updated explanation: verify token signature with key.")).toBeInTheDocument();
    expect(screen.getByText(/Original AI explanation:/i)).toBeInTheDocument();
    expect(screen.getByText(/Follow up with intern during weekly 1:1/i)).toBeInTheDocument();
  });
});

describe("Finding Edit Modal Flow", () => {
  it("submits edited payload with action EDIT", () => {
    const onSave = vi.fn();
    const onClose = vi.fn();

    render(
      <FindingEditModal
        finding={mockFinding}
        isOpen={true}
        onClose={onClose}
        onSave={onSave}
      />
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByDisplayValue(mockFinding.evidence_quote)).toBeInTheDocument();

    const explanationInput = screen.getByLabelText(/Educational Explanation & Context/i);
    fireEvent.change(explanationInput, { target: { value: "Updated custom mentor coaching note." } });

    const notesInput = screen.getByLabelText(/Mentor Coaching Notes/i);
    fireEvent.change(notesInput, { target: { value: "Coaching note for intern" } });

    const submitBtn = screen.getByRole("button", { name: /save & approve edit/i });
    fireEvent.click(submitBtn);

    expect(onSave).toHaveBeenCalledWith("finding-123", {
      action: "EDIT",
      edited_quote: mockFinding.evidence_quote,
      edited_explanation: "Updated custom mentor coaching note.",
      edited_suggested_fix: mockFinding.suggested_fix,
      edited_severity: "critical",
      mentor_notes: "Coaching note for intern",
    });
  });

  it("closes modal on cancel", () => {
    const onClose = vi.fn();
    render(
      <FindingEditModal
        finding={mockFinding}
        isOpen={true}
        onClose={onClose}
        onSave={vi.fn()}
      />
    );

    const cancelBtn = screen.getByRole("button", { name: /cancel/i });
    fireEvent.click(cancelBtn);

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe("Ingest Bar Client Validation", () => {
  it("rejects invalid PR URL format before submitting", () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <IngestBar />
        </BrowserRouter>
      </QueryClientProvider>
    );

    const input = screen.getByLabelText(/github pull request url/i);
    const submitBtn = screen.getByRole("button", { name: /analyze pr/i });

    fireEvent.change(input, { target: { value: "https://gitlab.com/wrong/host/pull/1" } });
    fireEvent.click(submitBtn);

    expect(screen.getByRole("alert")).toHaveTextContent(/Invalid PR URL/i);
  });
});
