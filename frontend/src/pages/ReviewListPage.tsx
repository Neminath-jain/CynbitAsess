import React, { useState } from "react";
import { Link } from "react-router-dom";
import { IngestBar } from "../components/IngestBar";
import { useReviewsList } from "../hooks/useReviews";

export const ReviewListPage: React.FC = () => {
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const { data: reviews, isLoading, isError, error, refetch } = useReviewsList(filter);

  const getStatusBadgeStyle = (status: string) => {
    switch (status) {
      case "APPROVED":
        return { bg: "var(--success-bg)", border: "var(--success-border)", text: "var(--success)" };
      case "REJECTED":
        return { bg: "var(--danger-bg)", border: "var(--danger-border)", text: "var(--danger)" };
      case "PENDING_APPROVAL":
      case "IN_REVIEW":
        return { bg: "var(--warning-bg)", border: "var(--warning-border)", text: "var(--warning)" };
      default:
        return { bg: "var(--bg-surface-elevated)", border: "var(--border-subtle)", text: "var(--text-muted)" };
    }
  };

  return (
    <main style={{ maxWidth: "1280px", margin: "0 auto", padding: "1.5rem" }}>
      <IngestBar />

      {/* Filter and Title Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-main)" }}>
            Intern Pull Request Reviews
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Staging queue for first-pass AI review comments awaiting mentor triage.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }} role="group" aria-label="Filter reviews by status">
          <button
            type="button"
            onClick={() => setFilter(undefined)}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-md)",
              fontSize: "0.8rem",
              fontWeight: 600,
              backgroundColor: filter === undefined ? "var(--primary)" : "var(--bg-surface)",
              color: filter === undefined ? "#ffffff" : "var(--text-muted)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            All Reviews
          </button>
          <button
            type="button"
            onClick={() => setFilter("PENDING_APPROVAL")}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-md)",
              fontSize: "0.8rem",
              fontWeight: 600,
              backgroundColor: filter === "PENDING_APPROVAL" ? "var(--primary)" : "var(--bg-surface)",
              color: filter === "PENDING_APPROVAL" ? "#ffffff" : "var(--text-muted)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            Pending Triage
          </button>
          <button
            type="button"
            onClick={() => setFilter("APPROVED")}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-md)",
              fontSize: "0.8rem",
              fontWeight: 600,
              backgroundColor: filter === "APPROVED" ? "var(--primary)" : "var(--bg-surface)",
              color: filter === "APPROVED" ? "#ffffff" : "var(--text-muted)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            Approved
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="animate-pulse"
              style={{
                height: "90px",
                backgroundColor: "var(--bg-surface)",
                borderRadius: "var(--radius-lg)",
                border: "1px solid var(--border-subtle)",
              }}
            />
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div
          role="alert"
          style={{
            padding: "1.5rem",
            backgroundColor: "var(--danger-bg)",
            border: "1px solid var(--danger-border)",
            borderRadius: "var(--radius-lg)",
            color: "var(--danger)",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: "0.5rem" }}>Error Loading Reviews</div>
          <p style={{ fontSize: "0.85rem", marginBottom: "1rem" }}>{error?.message || "Could not retrieve reviews"}</p>
          <button
            type="button"
            onClick={() => refetch()}
            style={{
              padding: "0.4rem 0.8rem",
              backgroundColor: "var(--danger)",
              color: "#fff",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.8rem",
              fontWeight: 600,
            }}
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && (!reviews || reviews.length === 0) && (
        <div
          style={{
            textAlign: "center",
            padding: "3.5rem 1.5rem",
            backgroundColor: "var(--bg-surface)",
            borderRadius: "var(--radius-lg)",
            border: "1px dashed var(--border-subtle)",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "0.75rem", color: "var(--text-dim)" }}>
            &#x1F50E;
          </div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-main)", marginBottom: "0.5rem" }}>
            No pull request reviews found
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", maxWidth: "480px", margin: "0 auto 1.5rem" }}>
            Paste a public GitHub Pull Request URL into the input bar above to ingest diffs, sanitize code, and stage AI review comments for mentor triage.
          </p>
        </div>
      )}

      {/* Reviews Table / Cards */}
      {!isLoading && !isError && reviews && reviews.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {reviews.map((r) => {
            const badge = getStatusBadgeStyle(r.status);
            return (
              <div
                key={r.id}
                style={{
                  backgroundColor: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-lg)",
                  padding: "1.25rem",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "1rem",
                  transition: "border-color 0.15s ease",
                }}
              >
                <div style={{ flex: 1, minWidth: "280px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.35rem" }}>
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        fontSize: "0.85rem",
                        color: "var(--info)",
                      }}
                    >
                      {r.repo_full_name}#{r.pr_number}
                    </span>
                    <span
                      style={{
                        fontSize: "0.7rem",
                        fontWeight: 700,
                        padding: "0.15rem 0.5rem",
                        borderRadius: "var(--radius-sm)",
                        backgroundColor: badge.bg,
                        border: `1px solid ${badge.border}`,
                        color: badge.text,
                      }}
                    >
                      {r.status}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
                      by @{r.author_username}
                    </span>
                  </div>

                  <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-main)", marginBottom: "0.4rem" }}>
                    {r.pr_title}
                  </h3>

                  <div style={{ display: "flex", gap: "1rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    <span>
                      Engine: <strong style={{ color: "var(--text-main)" }}>{r.provider} ({r.model})</strong>
                    </span>
                    <span>
                      Created: {new Date(r.created_at).toLocaleDateString()} {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-main)" }}>
                      {r.approved_count} / {r.findings_count}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>Approved Findings</div>
                  </div>

                  <Link
                    to={`/reviews/${r.id}`}
                    id={`open-review-${r.id}`}
                    style={{
                      padding: "0.6rem 1.2rem",
                      backgroundColor: "var(--primary)",
                      color: "#ffffff",
                      borderRadius: "var(--radius-md)",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                      display: "flex",
                      alignItems: "center",
                      gap: "0.4rem",
                      boxShadow: "0 2px 6px var(--primary-glow)",
                    }}
                  >
                    Open Triage &rarr;
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
};
