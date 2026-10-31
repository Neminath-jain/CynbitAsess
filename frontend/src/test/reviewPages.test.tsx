import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReviewListPage } from "../pages/ReviewListPage";
import { ReviewDetailPage } from "../pages/ReviewDetailPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import * as hooks from "../hooks/useReviews";
import type { ReviewResponse, ReviewListItemResponse } from "../api/client";

vi.mock("../hooks/useReviews");

const mockReviewItem: ReviewListItemResponse = {
  id: "rev-1",
  repo_full_name: "cynbit/bitelevate-sample",
  pr_number: 42,
  pr_title: "Add Payment Webhooks",
  author_username: "intern_alice",
  status: "PENDING_APPROVAL",
  provider: "mock",
  model: "mock-rules",
  findings_count: 3,
  approved_count: 1,
  created_at: "2026-10-31T10:00:00Z",
};

const mockDetailedReview: ReviewResponse = {
  id: "rev-1",
  repo_full_name: "cynbit/bitelevate-sample",
  pr_number: 42,
  pr_title: "Add Payment Webhooks",
  pr_description: "Implements stripe webhook processing",
  author_username: "intern_alice",
  base_commit_sha: "1111111111111111111111111111111111111111",
  head_commit_sha: "2222222222222222222222222222222222222222",
  status: "PENDING_APPROVAL",
  summary: "AI review generated 3 findings across 1 changed file.",
  raw_diff: "diff --git a/app/payment.py b/app/payment.py\n+ def process_payment():\n+     pass",
  is_truncated: false,
  provider: "mock",
  model: "mock-rules",
  latency_ms: 120,
  tokens: 450,
  est_cost: 0.0001,
  created_at: "2026-10-31T10:00:00Z",
  updated_at: "2026-10-31T10:00:00Z",
  findings: [
    {
      id: "f-1",
      review_id: "rev-1",
      rule_id: "SEC_HARDCODED_SECRET",
      severity: "critical",
      file: "app/payment.py",
      line_start: 10,
      line_end: 10,
      evidence_quote: "STRIPE_KEY = 'sk_live_12345'",
      explanation: "Hardcoded secret exposed in source code.",
      suggested_fix: "STRIPE_KEY = os.environ['STRIPE_KEY']",
      confidence: 1.0,
      created_at: "2026-10-31T10:00:00Z",
      decision: null,
    },
  ],
};

function renderWithClient(ui: React.ReactElement) {
  const testClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={testClient}>
      <MemoryRouter initialEntries={["/reviews/rev-1"]}>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Review List Page States", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders review list successfully with items", () => {
    vi.spyOn(hooks, "useReviewsList").mockReturnValue({
      data: [mockReviewItem],
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(hooks, "useCreateReviewMutation").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
    } as any);

    renderWithClient(<ReviewListPage />);

    expect(screen.getByText("Intern Pull Request Reviews")).toBeInTheDocument();
    expect(screen.getByText("cynbit/bitelevate-sample#42")).toBeInTheDocument();
    expect(screen.getByText("Add Payment Webhooks")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open triage/i })).toBeInTheDocument();
  });

  it("renders empty state when no reviews exist", () => {
    vi.spyOn(hooks, "useReviewsList").mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(hooks, "useCreateReviewMutation").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
    } as any);

    renderWithClient(<ReviewListPage />);

    expect(screen.getByText("No pull request reviews found")).toBeInTheDocument();
  });
});

describe("Review Detail Page States and Tabs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders split-pane review detail and switches between Diff and Rubric tabs", () => {
    vi.spyOn(hooks, "useReviewDetail").mockReturnValue({
      data: mockDetailedReview,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(hooks, "useRecordDecisionMutation").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);

    vi.spyOn(hooks, "useExportMarkdown").mockReturnValue({
      data: "# Approved Comments\n\nNone yet",
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    const testClient = new QueryClient();
    render(
      <QueryClientProvider client={testClient}>
        <MemoryRouter initialEntries={["/reviews/rev-1"]}>
          <Routes>
            <Route path="/reviews/:id" element={<ReviewDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText("Add Payment Webhooks")).toBeInTheDocument();
    expect(screen.getByText("SEC_HARDCODED_SECRET")).toBeInTheDocument();

    // Default right pane is Diff Viewer
    expect(screen.getByText("Pull Request Unified Diff")).toBeInTheDocument();

    // Switch to Rubric Summary tab
    const rubricTab = screen.getByRole("button", { name: "Rubric Summary" });
    fireEvent.click(rubricTab);

    expect(screen.getByText("Review Rubric & Telemetry Summary")).toBeInTheDocument();
    expect(screen.getByText(/Human Mentor Approval Gate: Active/i)).toBeInTheDocument();
  });

  it("renders error alert when review does not exist", () => {
    vi.spyOn(hooks, "useReviewDetail").mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new Error("Review not found"),
      refetch: vi.fn(),
    } as any);

    vi.spyOn(hooks, "useRecordDecisionMutation").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);

    const testClient = new QueryClient();
    render(
      <QueryClientProvider client={testClient}>
        <MemoryRouter initialEntries={["/reviews/invalid-id"]}>
          <Routes>
            <Route path="/reviews/:id" element={<ReviewDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Review Session Not Found");
  });
});

describe("NotFound Page", () => {
  it("renders 404 message and return link", () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>
    );

    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Page Not Found")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /return to review queue/i })).toBeInTheDocument();
  });
});
