import React, { useState } from "react";
import { useExportMarkdown } from "../hooks/useReviews";

interface ExportPreviewProps {
  reviewId: string;
}

export const ExportPreview: React.FC<ExportPreviewProps> = ({ reviewId }) => {
  const { data: markdown, isLoading, isError, error, refetch } = useExportMarkdown(reviewId, true);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!markdown) return;
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const handleDownload = () => {
    if (!markdown) return;
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `review-${reviewId.slice(0, 8)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        <div className="animate-pulse" style={{ fontSize: "1.2rem", marginBottom: "0.5rem" }}>
          &#x25CF; Generating Approved Markdown Export...
        </div>
        <p style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>
          Compiling exclusively human mentor-approved review comments.
        </p>
      </div>
    );
  }

  if (isError) {
    return (
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
        <div style={{ fontWeight: 600, marginBottom: "0.5rem" }}>Failed to generate export</div>
        <p style={{ fontSize: "0.85rem", marginBottom: "1rem" }}>{error?.message || "Unknown error"}</p>
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
          Retry Export
        </button>
      </div>
    );
  }

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface)",
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
          padding: "0.75rem 1.25rem",
          backgroundColor: "var(--bg-surface-elevated)",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <div style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--text-main)" }}>
            Approved Mentor Comments Export
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Filtered strictly to human mentor APPROVE / EDIT decisions.
          </div>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            id="copy-markdown-button"
            onClick={handleCopy}
            disabled={!markdown}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.75rem",
              fontWeight: 600,
              backgroundColor: copied ? "var(--success)" : "var(--primary)",
              color: "#ffffff",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              transition: "all 0.15s ease",
            }}
          >
            {copied ? "&#x2714; Copied to Clipboard!" : "Copy Markdown"}
          </button>

          <button
            type="button"
            id="download-markdown-button"
            onClick={handleDownload}
            disabled={!markdown}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.75rem",
              fontWeight: 600,
              backgroundColor: "var(--bg-base)",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-main)",
            }}
          >
            Download .md
          </button>
        </div>
      </div>

      <div style={{ padding: "1rem", overflowY: "auto", flex: 1, backgroundColor: "var(--bg-base)" }}>
        <pre
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.825rem",
            lineHeight: 1.6,
            color: "var(--text-main)",
            whiteSpace: "pre-wrap",
            margin: 0,
          }}
        >
          {markdown}
        </pre>
      </div>
    </div>
  );
};
