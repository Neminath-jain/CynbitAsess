import React from "react";
import { ReviewResponse } from "../api/client";

interface RubricSummaryProps {
  review: ReviewResponse;
}

export const RubricSummary: React.FC<RubricSummaryProps> = ({ review }) => {
  const findings = review.findings || [];

  // Group by rule ID
  const ruleCounts = findings.reduce<Record<string, number>>((acc, f) => {
    acc[f.rule_id] = (acc[f.rule_id] || 0) + 1;
    return acc;
  }, {});

  // Group by severity
  const severityCounts = findings.reduce<Record<string, number>>((acc, f) => {
    const s = f.severity.toUpperCase();
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  // Group by decision
  const approvedCount = findings.filter((f) => f.decision?.action === "APPROVE").length;
  const editedCount = findings.filter((f) => f.decision?.action === "EDIT").length;
  const rejectedCount = findings.filter((f) => f.decision?.action === "REJECT").length;
  const pendingCount = findings.filter((f) => !f.decision).length;

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.5rem",
      }}
    >
      <div>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.25rem" }}>
          Review Rubric & Telemetry Summary
        </h3>
        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          Telemetry metrics and rule enforcement breakdown for {review.repo_full_name}#{review.pr_number}.
        </p>
      </div>

      {/* Human Mentor Gate Status Card */}
      <div
        style={{
          padding: "1rem",
          borderRadius: "var(--radius-md)",
          backgroundColor: "rgba(16, 185, 129, 0.08)",
          border: "1px solid var(--success-border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div>
          <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--success)" }}>
            &#x2714; Human Mentor Approval Gate: Active
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Zero unapproved AI comments can reach the BitElevate intern or GitHub PR.
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-main)" }}>
            {approvedCount + editedCount} / {findings.length}
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>Approved Comments</div>
        </div>
      </div>

      {/* Triage Progress Breakdown */}
      <div>
        <h4 style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
          Mentor Triage Progress
        </h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.75rem" }}>
          <div style={{ padding: "0.75rem", backgroundColor: "var(--bg-base)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--warning)" }}>{pendingCount}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Pending</div>
          </div>
          <div style={{ padding: "0.75rem", backgroundColor: "var(--bg-base)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--success)" }}>{approvedCount}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Approved</div>
          </div>
          <div style={{ padding: "0.75rem", backgroundColor: "var(--bg-base)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--info)" }}>{editedCount}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Edited</div>
          </div>
          <div style={{ padding: "0.75rem", backgroundColor: "var(--bg-base)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--danger)" }}>{rejectedCount}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Rejected</div>
          </div>
        </div>
      </div>

      {/* Severity Breakdown */}
      <div>
        <h4 style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
          Severity Distribution
        </h4>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          {Object.entries(severityCounts).map(([sev, cnt]) => (
            <div
              key={sev}
              style={{
                padding: "0.4rem 0.8rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-base)",
                border: "1px solid var(--border-subtle)",
                fontSize: "0.8rem",
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              <span style={{ fontWeight: 600, color: "var(--text-main)" }}>{sev}:</span>
              <span style={{ color: "var(--info)", fontWeight: 700 }}>{cnt}</span>
            </div>
          ))}
          {findings.length === 0 && (
            <div style={{ fontSize: "0.8rem", color: "var(--text-dim)", fontStyle: "italic" }}>
              No findings present.
            </div>
          )}
        </div>
      </div>

      {/* Rules Distribution */}
      <div>
        <h4 style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
          Triggered Engineering Rules
        </h4>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {Object.entries(ruleCounts).map(([ruleId, count]) => (
            <div
              key={ruleId}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "0.6rem 0.75rem",
                backgroundColor: "var(--bg-base)",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", color: "var(--text-main)" }}>
                {ruleId}
              </span>
              <span
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  backgroundColor: "var(--bg-surface-elevated)",
                  padding: "0.2rem 0.5rem",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--primary)",
                }}
              >
                {count} {count === 1 ? "finding" : "findings"}
              </span>
            </div>
          ))}
          {findings.length === 0 && (
            <div style={{ fontSize: "0.8rem", color: "var(--text-dim)", fontStyle: "italic" }}>
              No rule violations identified in this pull request.
            </div>
          )}
        </div>
      </div>

      {/* Telemetry Grid */}
      <div>
        <h4 style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
          Engine Attribution & Performance
        </h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "0.75rem" }}>
          <div style={{ padding: "0.75rem", backgroundColor: "var(--bg-base)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>LLM Provider & Model</div>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-main)", marginTop: "0.2rem" }}>
              {review.provider} ({review.model})
            </div>
          </div>
          <div style={{ padding: "0.75rem", backgroundColor: "var(--bg-base)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>Latency</div>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-main)", marginTop: "0.2rem" }}>
              {review.latency_ms} ms
            </div>
          </div>
          <div style={{ padding: "0.75rem", backgroundColor: "var(--bg-base)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>Tokens & Estimated Cost</div>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-main)", marginTop: "0.2rem" }}>
              {review.tokens} tokens &bull; ${review.est_cost.toFixed(4)}
            </div>
          </div>
          <div style={{ padding: "0.75rem", backgroundColor: "var(--bg-base)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>Diff Truncation</div>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, color: review.is_truncated ? "var(--warning)" : "var(--success)", marginTop: "0.2rem" }}>
              {review.is_truncated ? "Truncated (Exceeded cap)" : "Full diff analyzed"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
