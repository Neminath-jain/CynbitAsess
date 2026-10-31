import React from "react";
import { FindingResponse } from "../api/client";

interface DiffViewerProps {
  rawDiff: string;
  selectedFinding: FindingResponse | null;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ rawDiff, selectedFinding }) => {
  if (!rawDiff || !rawDiff.trim()) {
    return (
      <div
        style={{
          padding: "2rem",
          textAlign: "center",
          color: "var(--text-dim)",
          backgroundColor: "var(--bg-base)",
          borderRadius: "var(--radius-lg)",
          border: "1px dashed var(--border-subtle)",
        }}
      >
        No git diff content available for this review session.
      </div>
    );
  }

  const lines = rawDiff.split("\n");

  return (
    <div
      style={{
        backgroundColor: "var(--bg-base)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        maxHeight: "750px",
      }}
    >
      <div
        style={{
          padding: "0.5rem 1rem",
          backgroundColor: "var(--bg-surface)",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.75rem",
          color: "var(--text-muted)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontWeight: 600 }}>Pull Request Unified Diff</span>
          {selectedFinding && (
            <span
              style={{
                backgroundColor: "var(--bg-surface-elevated)",
                padding: "0.15rem 0.5rem",
                borderRadius: "var(--radius-sm)",
                color: "var(--info)",
                fontFamily: "var(--font-mono)",
              }}
            >
              Focusing: {selectedFinding.file} (L{selectedFinding.line_start})
            </span>
          )}
        </div>
        <div>{lines.length} lines</div>
      </div>

      <div
        style={{
          overflowY: "auto",
          overflowX: "auto",
          fontFamily: "var(--font-mono)",
          fontSize: "0.8rem",
          lineHeight: 1.5,
          padding: "0.5rem 0",
        }}
      >
        {lines.map((line, idx) => {
          let lineBg = "transparent";
          let textColor = "var(--text-muted)";
          let indicatorColor = "var(--text-dim)";

          if (line.startsWith("diff --git") || line.startsWith("index ")) {
            lineBg = "rgba(99, 102, 241, 0.08)";
            textColor = "var(--primary)";
          } else if (line.startsWith("@@")) {
            lineBg = "rgba(59, 130, 246, 0.08)";
            textColor = "var(--info)";
          } else if (line.startsWith("+")) {
            lineBg = "rgba(16, 185, 129, 0.12)";
            textColor = "#a7f3d0";
            indicatorColor = "var(--success)";
          } else if (line.startsWith("-")) {
            lineBg = "rgba(239, 68, 68, 0.12)";
            textColor = "#fecaca";
            indicatorColor = "var(--danger)";
          }

          // Check if this line matches selected finding evidence
          const isEvidenceMatch =
            selectedFinding &&
            line.includes(selectedFinding.evidence_quote.trim()) &&
            selectedFinding.evidence_quote.trim().length > 3;

          if (isEvidenceMatch) {
            lineBg = "rgba(245, 158, 11, 0.25)";
            textColor = "#fef08a";
          }

          return (
            <div
              key={idx}
              style={{
                display: "flex",
                backgroundColor: lineBg,
                padding: "0 0.5rem",
                borderLeft: isEvidenceMatch ? "3px solid var(--warning)" : "3px solid transparent",
              }}
            >
              <span
                style={{
                  width: "45px",
                  color: indicatorColor,
                  userSelect: "none",
                  textAlign: "right",
                  paddingRight: "0.75rem",
                  fontSize: "0.75rem",
                }}
              >
                {idx + 1}
              </span>
              <pre
                style={{
                  margin: 0,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  color: textColor,
                  flex: 1,
                }}
              >
                {line || " "}
              </pre>
            </div>
          );
        })}
      </div>
    </div>
  );
};
