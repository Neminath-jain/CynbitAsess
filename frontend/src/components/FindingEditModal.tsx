import React, { useEffect, useState } from "react";
import { DecisionRequest, FindingResponse } from "../api/client";

interface FindingEditModalProps {
  finding: FindingResponse | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (findingId: string, decision: DecisionRequest) => void;
  isSubmitting?: boolean;
}

export const FindingEditModal: React.FC<FindingEditModalProps> = ({
  finding,
  isOpen,
  onClose,
  onSave,
  isSubmitting = false,
}) => {
  const [quote, setQuote] = useState("");
  const [explanation, setExplanation] = useState("");
  const [suggestedFix, setSuggestedFix] = useState("");
  const [severity, setSeverity] = useState("suggestion");
  const [mentorNotes, setMentorNotes] = useState("");

  useEffect(() => {
    if (finding) {
      const d = finding.decision;
      setQuote(d?.edited_quote || finding.evidence_quote);
      setExplanation(d?.edited_explanation || finding.explanation);
      setSuggestedFix(d?.edited_suggested_fix || finding.suggested_fix);
      setSeverity((d?.edited_severity || finding.severity).toLowerCase());
      setMentorNotes(d?.mentor_notes || "");
    }
  }, [finding]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !finding) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(finding.id, {
      action: "EDIT",
      edited_quote: quote.trim() || undefined,
      edited_explanation: explanation.trim() || undefined,
      edited_suggested_fix: suggestedFix.trim() || undefined,
      edited_severity: severity.trim() || undefined,
      mentor_notes: mentorNotes.trim() || undefined,
    });
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-modal-title"
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
        padding: "1rem",
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-xl)",
          width: "100%",
          maxWidth: "680px",
          maxHeight: "90vh",
          display: "flex",
          flexDirection: "column",
          boxShadow: "var(--shadow-lg)",
          overflow: "hidden",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "1.25rem 1.5rem",
            borderBottom: "1px solid var(--border-subtle)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h3 id="edit-modal-title" style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-main)" }}>
              Edit Review Comment & Pedagogical Guidance
            </h3>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
              {finding.rule_id} &bull; {finding.file}:L{finding.line_start}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              padding: "0.4rem",
              borderRadius: "var(--radius-sm)",
              color: "var(--text-muted)",
              fontSize: "1.2rem",
              lineHeight: 1,
            }}
          >
            &times;
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ overflowY: "auto", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label htmlFor="edit-severity" style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.35rem" }}>
              Severity Level
            </label>
            <select
              id="edit-severity"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-base)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-main)",
                fontSize: "0.85rem",
              }}
            >
              <option value="critical">Critical / Blocker</option>
              <option value="warning">Warning / Major</option>
              <option value="suggestion">Suggestion / Minor</option>
              <option value="note">Note / Style</option>
            </select>
          </div>

          <div>
            <label htmlFor="edit-quote" style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.35rem" }}>
              Evidence Quote (Must appear in diff)
            </label>
            <textarea
              id="edit-quote"
              rows={2}
              value={quote}
              onChange={(e) => setQuote(e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-base)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-main)",
                fontSize: "0.85rem",
                fontFamily: "var(--font-mono)",
              }}
            />
          </div>

          <div>
            <label htmlFor="edit-explanation" style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.35rem" }}>
              Educational Explanation & Context
            </label>
            <textarea
              id="edit-explanation"
              rows={3}
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-base)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-main)",
                fontSize: "0.85rem",
                lineHeight: 1.4,
              }}
            />
          </div>

          <div>
            <label htmlFor="edit-suggested-fix" style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.35rem" }}>
              Suggested Code Fix
            </label>
            <textarea
              id="edit-suggested-fix"
              rows={3}
              value={suggestedFix}
              onChange={(e) => setSuggestedFix(e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-base)",
                border: "1px solid var(--border-subtle)",
                color: "var(--success)",
                fontSize: "0.85rem",
                fontFamily: "var(--font-mono)",
              }}
            />
          </div>

          <div>
            <label htmlFor="edit-mentor-notes" style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--primary)", marginBottom: "0.35rem" }}>
              Mentor Coaching Notes (Optional internal guidance)
            </label>
            <input
              id="edit-mentor-notes"
              type="text"
              placeholder="e.g. Discuss in 1:1 on Monday regarding database indexes"
              value={mentorNotes}
              onChange={(e) => setMentorNotes(e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-base)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-main)",
                fontSize: "0.85rem",
              }}
            />
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              gap: "0.75rem",
              marginTop: "0.5rem",
              borderTop: "1px solid var(--border-subtle)",
              paddingTop: "1rem",
            }}
          >
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              style={{
                padding: "0.5rem 1rem",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-muted)",
                fontSize: "0.85rem",
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              id="save-edit-button"
              disabled={isSubmitting}
              style={{
                padding: "0.5rem 1.25rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--info)",
                color: "#ffffff",
                fontSize: "0.85rem",
                fontWeight: 600,
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              {isSubmitting ? "Saving..." : "Save & Approve Edit"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
