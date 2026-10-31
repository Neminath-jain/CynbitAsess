import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { DecisionRequest, FindingResponse } from "../api/client";
import { DiffViewer } from "../components/DiffViewer";
import { ExportPreview } from "../components/ExportPreview";
import { FindingCard } from "../components/FindingCard";
import { FindingEditModal } from "../components/FindingEditModal";
import { RubricSummary } from "../components/RubricSummary";
import { useRecordDecisionMutation, useReviewDetail } from "../hooks/useReviews";

export const ReviewDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: review, isLoading, isError, error, refetch } = useReviewDetail(id);
  const decisionMutation = useRecordDecisionMutation(id);

  const [activeTab, setActiveTab] = useState<"diff" | "rubric" | "export">("diff");
  const [selectedFindingIndex, setSelectedFindingIndex] = useState<number>(0);
  const [findingFilter, setFindingFilter] = useState<"ALL" | "PENDING" | "APPROVED" | "REJECTED">("ALL");
  const [editingFinding, setEditingFinding] = useState<FindingResponse | null>(null);

  const findings = review?.findings || [];

  const filteredFindings = findings.filter((f) => {
    if (findingFilter === "PENDING") return !f.decision;
    if (findingFilter === "APPROVED") return f.decision?.action === "APPROVE" || f.decision?.action === "EDIT";
    if (findingFilter === "REJECTED") return f.decision?.action === "REJECT";
    return true;
  });

  const activeFinding = filteredFindings[selectedFindingIndex] || filteredFindings[0] || null;

  // Keyboard navigation & triage shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts if focus is inside an input, textarea, or select
      const target = e.target as HTMLElement;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
      if (editingFinding) return; // disable when edit modal is open

      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedFindingIndex((prev) => Math.min(prev + 1, filteredFindings.length - 1));
      } else if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedFindingIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "a" || e.key === "A") {
        if (activeFinding) {
          e.preventDefault();
          handleApprove(activeFinding);
        }
      } else if (e.key === "e" || e.key === "E") {
        if (activeFinding) {
          e.preventDefault();
          setEditingFinding(activeFinding);
        }
      } else if (e.key === "r" || e.key === "R") {
        if (activeFinding) {
          e.preventDefault();
          handleReject(activeFinding);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [filteredFindings, activeFinding, editingFinding]);

  const handleApprove = (finding: FindingResponse) => {
    decisionMutation.mutate({
      findingId: finding.id,
      decision: { action: "APPROVE" },
    });
  };

  const handleReject = (finding: FindingResponse) => {
    decisionMutation.mutate({
      findingId: finding.id,
      decision: { action: "REJECT" },
    });
  };

  const handleSaveEdit = (findingId: string, decision: DecisionRequest) => {
    decisionMutation.mutate(
      { findingId, decision },
      {
        onSuccess: () => {
          setEditingFinding(null);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <main style={{ maxWidth: "1600px", margin: "0 auto", padding: "1.5rem" }}>
        <div className="animate-pulse" style={{ height: "40px", width: "240px", backgroundColor: "var(--bg-surface)", borderRadius: "var(--radius-md)", marginBottom: "1.5rem" }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
          <div className="animate-pulse" style={{ height: "600px", backgroundColor: "var(--bg-surface)", borderRadius: "var(--radius-lg)" }} />
          <div className="animate-pulse" style={{ height: "600px", backgroundColor: "var(--bg-surface)", borderRadius: "var(--radius-lg)" }} />
        </div>
      </main>
    );
  }

  if (isError || !review) {
    return (
      <main style={{ maxWidth: "800px", margin: "3rem auto", padding: "1.5rem" }}>
        <div
          role="alert"
          style={{
            padding: "2rem",
            backgroundColor: "var(--danger-bg)",
            border: "1px solid var(--danger-border)",
            borderRadius: "var(--radius-lg)",
            color: "var(--danger)",
            textAlign: "center",
          }}
        >
          <h2 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
            Review Session Not Found
          </h2>
          <p style={{ fontSize: "0.85rem", marginBottom: "1.5rem" }}>
            {error?.message || "Could not load the requested review session."}
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: "1rem" }}>
            <button
              type="button"
              onClick={() => refetch()}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "var(--danger)",
                color: "#fff",
                borderRadius: "var(--radius-sm)",
                fontWeight: 600,
                fontSize: "0.85rem",
              }}
            >
              Retry
            </button>
            <Link
              to="/"
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-main)",
                borderRadius: "var(--radius-sm)",
                fontSize: "0.85rem",
              }}
            >
              &larr; Back to Queue
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: "1600px", margin: "0 auto", padding: "1.25rem 1.5rem" }}>
      {/* Top Breadcrumb & Metadata Header */}
      <div
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "1rem 1.25rem",
          marginBottom: "1rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.3rem" }}>
            <Link
              to="/"
              style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.25rem" }}
            >
              &larr; Reviews Queue
            </Link>
            <span style={{ color: "var(--text-dim)" }}>/</span>
            <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: "0.9rem", color: "var(--info)" }}>
              {review.repo_full_name}#{review.pr_number}
            </span>
            <span
              style={{
                fontSize: "0.7rem",
                fontWeight: 700,
                padding: "0.15rem 0.5rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: review.status === "APPROVED" ? "var(--success-bg)" : "var(--warning-bg)",
                border: `1px solid ${review.status === "APPROVED" ? "var(--success-border)" : "var(--warning-border)"}`,
                color: review.status === "APPROVED" ? "var(--success)" : "var(--warning)",
              }}
            >
              {review.status}
            </span>
          </div>

          <h1 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-main)" }}>
            {review.pr_title}
          </h1>

          <div style={{ display: "flex", gap: "1rem", fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.25rem" }}>
            <span>Author: <strong>@{review.author_username}</strong></span>
            <span>Attribution: <strong>{review.provider} ({review.model})</strong></span>
            <span>Latency: <strong>{review.latency_ms}ms</strong></span>
            <span>Tokens: <strong>{review.tokens}</strong></span>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button
            type="button"
            id="tab-export-button"
            onClick={() => setActiveTab("export")}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "var(--radius-md)",
              fontSize: "0.8rem",
              fontWeight: 600,
              backgroundColor: activeTab === "export" ? "var(--primary)" : "var(--bg-surface-elevated)",
              border: "1px solid var(--border-subtle)",
              color: "#ffffff",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            &#x1F4CB; Export Approved ({findings.filter((f) => f.decision?.action === "APPROVE" || f.decision?.action === "EDIT").length})
          </button>
        </div>
      </div>

      {/* Split-Pane Layout: Left Findings, Right Workspace (Diff / Rubric / Export) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(420px, 1fr) minmax(460px, 1.2fr)",
          gap: "1.25rem",
          alignItems: "start",
        }}
      >
        {/* Left Pane: Findings Stream */}
        <section aria-label="Review findings stream" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {/* Finding Filter Tabs & Keyboard Hint */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "0.5rem",
              backgroundColor: "var(--bg-surface)",
              padding: "0.6rem 0.8rem",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ display: "flex", gap: "0.3rem" }}>
              {(["ALL", "PENDING", "APPROVED", "REJECTED"] as const).map((filter) => (
                <button
                  key={filter}
                  type="button"
                  onClick={() => {
                    setFindingFilter(filter);
                    setSelectedFindingIndex(0);
                  }}
                  style={{
                    padding: "0.25rem 0.55rem",
                    borderRadius: "var(--radius-sm)",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    backgroundColor: findingFilter === filter ? "var(--primary)" : "transparent",
                    color: findingFilter === filter ? "#ffffff" : "var(--text-muted)",
                  }}
                >
                  {filter}
                </button>
              ))}
            </div>

            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", display: "flex", gap: "0.4rem" }}>
              <span>Hotkeys:</span>
              <kbd style={{ backgroundColor: "var(--bg-base)", padding: "0.1rem 0.3rem", borderRadius: "3px", border: "1px solid var(--border-subtle)" }}>J/K</kbd>
              <kbd style={{ backgroundColor: "var(--bg-base)", padding: "0.1rem 0.3rem", borderRadius: "3px", border: "1px solid var(--border-subtle)" }}>A</kbd>
              <kbd style={{ backgroundColor: "var(--bg-base)", padding: "0.1rem 0.3rem", borderRadius: "3px", border: "1px solid var(--border-subtle)" }}>E</kbd>
              <kbd style={{ backgroundColor: "var(--bg-base)", padding: "0.1rem 0.3rem", borderRadius: "3px", border: "1px solid var(--border-subtle)" }}>R</kbd>
            </div>
          </div>

          {/* Finding Cards */}
          {filteredFindings.length === 0 ? (
            <div
              style={{
                padding: "3rem 1.5rem",
                textAlign: "center",
                backgroundColor: "var(--bg-surface)",
                borderRadius: "var(--radius-lg)",
                border: "1px dashed var(--border-subtle)",
                color: "var(--text-muted)",
              }}
            >
              No findings matching the &ldquo;{findingFilter}&rdquo; filter.
            </div>
          ) : (
            filteredFindings.map((finding, idx) => (
              <FindingCard
                key={finding.id}
                finding={finding}
                index={idx}
                isSelected={idx === selectedFindingIndex}
                onSelect={() => setSelectedFindingIndex(idx)}
                onApprove={() => handleApprove(finding)}
                onEdit={() => setEditingFinding(finding)}
                onReject={() => handleReject(finding)}
                isSubmitting={decisionMutation.isPending}
              />
            ))
          )}
        </section>

        {/* Right Pane: Workspace Tabs (Diff Viewer / Rubric / Export) */}
        <section aria-label="Review workspace" style={{ position: "sticky", top: "4.5rem" }}>
          {/* Workspace Tabs Header */}
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              marginBottom: "0.75rem",
              borderBottom: "1px solid var(--border-subtle)",
              paddingBottom: "0.5rem",
            }}
          >
            <button
              type="button"
              id="tab-diff"
              onClick={() => setActiveTab("diff")}
              style={{
                padding: "0.5rem 1rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.85rem",
                fontWeight: 600,
                backgroundColor: activeTab === "diff" ? "var(--bg-surface-elevated)" : "transparent",
                color: activeTab === "diff" ? "var(--text-main)" : "var(--text-muted)",
                border: activeTab === "diff" ? "1px solid var(--border-subtle)" : "1px solid transparent",
              }}
            >
              Git Diff Viewer
            </button>
            <button
              type="button"
              id="tab-rubric"
              onClick={() => setActiveTab("rubric")}
              style={{
                padding: "0.5rem 1rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.85rem",
                fontWeight: 600,
                backgroundColor: activeTab === "rubric" ? "var(--bg-surface-elevated)" : "transparent",
                color: activeTab === "rubric" ? "var(--text-main)" : "var(--text-muted)",
                border: activeTab === "rubric" ? "1px solid var(--border-subtle)" : "1px solid transparent",
              }}
            >
              Rubric Summary
            </button>
            <button
              type="button"
              id="tab-export"
              onClick={() => setActiveTab("export")}
              style={{
                padding: "0.5rem 1rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.85rem",
                fontWeight: 600,
                backgroundColor: activeTab === "export" ? "var(--bg-surface-elevated)" : "transparent",
                color: activeTab === "export" ? "var(--text-main)" : "var(--text-muted)",
                border: activeTab === "export" ? "1px solid var(--border-subtle)" : "1px solid transparent",
              }}
            >
              Approved Export
            </button>
          </div>

          {/* Active Workspace View */}
          {activeTab === "diff" && (
            <DiffViewer rawDiff={review.raw_diff} selectedFinding={activeFinding} />
          )}

          {activeTab === "rubric" && (
            <RubricSummary review={review} />
          )}

          {activeTab === "export" && (
            <ExportPreview reviewId={review.id} />
          )}
        </section>
      </div>

      {/* Edit Modal */}
      <FindingEditModal
        finding={editingFinding}
        isOpen={Boolean(editingFinding)}
        onClose={() => setEditingFinding(null)}
        onSave={handleSaveEdit}
        isSubmitting={decisionMutation.isPending}
      />
    </main>
  );
};
