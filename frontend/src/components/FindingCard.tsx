import React from "react";
import { FindingResponse } from "../api/client";

interface FindingCardProps {
  finding: FindingResponse;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
  onApprove: () => void;
  onEdit: () => void;
  onReject: () => void;
  isSubmitting?: boolean;
}

export const FindingCard: React.FC<FindingCardProps> = ({
  finding,
  index,
  isSelected,
  onSelect,
  onApprove,
  onEdit,
  onReject,
  isSubmitting = false,
}) => {
  const decision = finding.decision;
  const isApproved = decision?.action === "APPROVE";
  const isEdited = decision?.action === "EDIT";
  const isRejected = decision?.action === "REJECT";
  const isDecided = Boolean(decision);

  const getSeverityStyle = (severity: string) => {
    const s = severity.toUpperCase();
    if (s.includes("CRITICAL") || s.includes("BLOCKER")) {
      return { bg: "var(--danger-bg)", border: "var(--danger-border)", text: "var(--danger)" };
    }
    if (s.includes("WARN") || s.includes("MAJOR")) {
      return { bg: "var(--warning-bg)", border: "var(--warning-border)", text: "var(--warning)" };
    }
    if (s.includes("SUGGESTION") || s.includes("MINOR")) {
      return { bg: "var(--info-bg)", border: "var(--info-border)", text: "var(--info)" };
    }
    return { bg: "var(--success-bg)", border: "var(--success-border)", text: "var(--success)" };
  };

  const activeSeverity = (isEdited && decision?.edited_severity) || finding.severity;
  const sevStyle = getSeverityStyle(activeSeverity);

  return (
    <article
      id={`finding-card-${finding.id}`}
      onClick={onSelect}
      tabIndex={0}
      aria-label={`Finding ${index + 1}: ${finding.rule_id} in ${finding.file}`}
      style={{
        backgroundColor: "var(--bg-surface)",
        border: `1px solid ${isSelected ? "var(--border-focus)" : "var(--border-subtle)"}`,
        borderRadius: "var(--radius-lg)",
        padding: "1.25rem",
        marginBottom: "1rem",
        boxShadow: isSelected ? "0 0 0 2px var(--primary-glow), var(--shadow-md)" : "var(--shadow-sm)",
        transition: "border-color 0.15s ease, box-shadow 0.15s ease",
        outline: "none",
        cursor: "pointer",
        position: "relative",
      }}
    >
      {/* Top Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem", gap: "0.5rem" }}>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.5rem" }}>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 700,
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
              backgroundColor: "var(--bg-surface-elevated)",
              padding: "0.2rem 0.5rem",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            #{index + 1}
          </span>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 700,
              fontFamily: "var(--font-mono)",
              color: "var(--text-main)",
              backgroundColor: "var(--bg-surface-elevated)",
              padding: "0.2rem 0.55rem",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            {finding.rule_id}
          </span>
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 700,
              textTransform: "uppercase",
              padding: "0.2rem 0.5rem",
              borderRadius: "var(--radius-sm)",
              backgroundColor: sevStyle.bg,
              border: `1px solid ${sevStyle.border}`,
              color: sevStyle.text,
            }}
          >
            {activeSeverity.toUpperCase()}
          </span>
        </div>

        {/* Decision Badge */}
        <div>
          {isApproved && (
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--success)",
                backgroundColor: "var(--success-bg)",
                border: "1px solid var(--success-border)",
                padding: "0.25rem 0.6rem",
                borderRadius: "var(--radius-sm)",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.3rem",
              }}
            >
              &#x2713; Approved
            </span>
          )}
          {isEdited && (
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--info)",
                backgroundColor: "var(--info-bg)",
                border: "1px solid var(--info-border)",
                padding: "0.25rem 0.6rem",
                borderRadius: "var(--radius-sm)",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.3rem",
              }}
            >
              &#x270E; Edited & Approved
            </span>
          )}
          {isRejected && (
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--danger)",
                backgroundColor: "var(--danger-bg)",
                border: "1px solid var(--danger-border)",
                padding: "0.25rem 0.6rem",
                borderRadius: "var(--radius-sm)",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.3rem",
              }}
            >
              &#x2715; Rejected
            </span>
          )}
          {!isDecided && (
            <span
              style={{
                fontSize: "0.75rem",
                color: "var(--warning)",
                backgroundColor: "var(--warning-bg)",
                border: "1px solid var(--warning-border)",
                padding: "0.25rem 0.6rem",
                borderRadius: "var(--radius-sm)",
              }}
            >
              Pending Mentor Triage
            </span>
          )}
        </div>
      </div>

      {/* File & Line Location */}
      <div
        style={{
          fontSize: "0.825rem",
          fontFamily: "var(--font-mono)",
          color: "var(--text-dim)",
          marginBottom: "0.75rem",
          display: "flex",
          alignItems: "center",
          gap: "0.35rem",
        }}
      >
        <span style={{ color: "var(--info)" }}>{finding.file}</span>
        <span>:</span>
        <span>L{finding.line_start}{finding.line_end !== finding.line_start ? `-L${finding.line_end}` : ""}</span>
      </div>

      {/* Evidence Quote */}
      <div style={{ marginBottom: "0.85rem" }}>
        <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>
          Evidence Quote from PR Diff:
        </div>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.825rem",
            backgroundColor: "var(--bg-base)",
            borderLeft: "3px solid var(--info)",
            padding: "0.5rem 0.75rem",
            borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
            color: "var(--text-main)",
            whiteSpace: "pre-wrap",
            overflowX: "auto",
          }}
        >
          {isEdited && decision?.edited_quote ? decision.edited_quote : finding.evidence_quote}
        </div>
        {isEdited && decision?.edited_quote && decision.original_quote !== decision.edited_quote && (
          <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "0.25rem", fontStyle: "italic" }}>
            Original AI quote: &ldquo;{decision.original_quote}&rdquo;
          </div>
        )}
      </div>

      {/* Pedagogical Explanation */}
      <div style={{ marginBottom: "0.85rem" }}>
        <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>
          Educational Rationale:
        </div>
        <p style={{ fontSize: "0.85rem", color: "var(--text-main)", lineHeight: 1.5 }}>
          {isEdited && decision?.edited_explanation ? decision.edited_explanation : finding.explanation}
        </p>
        {isEdited && decision?.edited_explanation && decision.original_explanation !== decision.edited_explanation && (
          <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "0.25rem", fontStyle: "italic" }}>
            Original AI explanation: {decision.original_explanation}
          </div>
        )}
      </div>

      {/* Suggested Fix */}
      <div style={{ marginBottom: "1rem" }}>
        <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>
          Suggested Fix:
        </div>
        <pre
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.8rem",
            backgroundColor: "var(--bg-base)",
            border: "1px solid var(--border-subtle)",
            padding: "0.6rem 0.75rem",
            borderRadius: "var(--radius-sm)",
            color: "var(--success)",
            whiteSpace: "pre-wrap",
            overflowX: "auto",
          }}
        >
          {isEdited && decision?.edited_suggested_fix ? decision.edited_suggested_fix : finding.suggested_fix}
        </pre>
      </div>

      {/* Mentor Notes (if any) */}
      {decision?.mentor_notes && (
        <div
          style={{
            marginBottom: "1rem",
            padding: "0.5rem 0.75rem",
            backgroundColor: "rgba(99, 102, 241, 0.08)",
            border: "1px solid rgba(99, 102, 241, 0.2)",
            borderRadius: "var(--radius-sm)",
            fontSize: "0.8rem",
          }}
        >
          <span style={{ fontWeight: 600, color: "var(--primary)" }}>Mentor Coaching Note: </span>
          <span style={{ color: "var(--text-main)" }}>{decision.mentor_notes}</span>
        </div>
      )}

      {/* Triage Actions */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderTop: "1px solid var(--border-subtle)",
          paddingTop: "0.75rem",
          gap: "0.5rem",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
          Confidence: {(finding.confidence * 100).toFixed(0)}%
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            id={`approve-button-${finding.id}`}
            onClick={onApprove}
            disabled={isSubmitting}
            aria-label={`Approve finding ${index + 1}`}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.8rem",
              fontWeight: 600,
              backgroundColor: isApproved ? "var(--success)" : "rgba(16, 185, 129, 0.15)",
              color: isApproved ? "#ffffff" : "var(--success)",
              border: "1px solid var(--success-border)",
              transition: "all 0.15s ease",
            }}
          >
            &#x2713; Approve
          </button>

          <button
            type="button"
            id={`edit-button-${finding.id}`}
            onClick={onEdit}
            disabled={isSubmitting}
            aria-label={`Edit finding ${index + 1}`}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.8rem",
              fontWeight: 600,
              backgroundColor: isEdited ? "var(--info)" : "rgba(59, 130, 246, 0.15)",
              color: isEdited ? "#ffffff" : "var(--info)",
              border: "1px solid var(--info-border)",
              transition: "all 0.15s ease",
            }}
          >
            &#x270E; Edit
          </button>

          <button
            type="button"
            id={`reject-button-${finding.id}`}
            onClick={onReject}
            disabled={isSubmitting}
            aria-label={`Reject finding ${index + 1}`}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.8rem",
              fontWeight: 600,
              backgroundColor: isRejected ? "var(--danger)" : "rgba(100, 116, 139, 0.15)",
              color: isRejected ? "#ffffff" : "var(--text-muted)",
              border: "1px solid var(--border-subtle)",
              transition: "all 0.15s ease",
            }}
          >
            &#x2715; Reject
          </button>
        </div>
      </div>
    </article>
  );
};
