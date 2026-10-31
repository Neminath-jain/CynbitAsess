import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateReviewMutation } from "../hooks/useReviews";

export const IngestBar: React.FC = () => {
  const [prUrl, setPrUrl] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const navigate = useNavigate();
  const createMutation = useCreateReviewMutation();

  const validateUrl = (url: string): boolean => {
    const trimmed = url.trim();
    const githubPrPattern = /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/pull\/[0-9]+$/;
    if (!githubPrPattern.test(trimmed)) {
      setValidationError("Invalid PR URL. Must be in the format: https://github.com/{owner}/{repo}/pull/{number}");
      return false;
    }
    setValidationError(null);
    return true;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateUrl(prUrl)) return;

    createMutation.mutate(prUrl.trim(), {
      onSuccess: (data) => {
        setPrUrl("");
        navigate(`/reviews/${data.id}`);
      },
    });
  };

  const handleSetExample = (exampleUrl: string) => {
    setPrUrl(exampleUrl);
    setValidationError(null);
  };

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "1.25rem",
        marginBottom: "1.5rem",
        boxShadow: "var(--shadow-sm)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.75rem" }}>
        <div>
          <h2 style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--text-main)" }}>
            Analyze New Intern Pull Request
          </h2>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Trigger first-pass AI review with untrusted diff containment, evidence checks, and human mentor staging.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Sample Fixtures:</span>
          <button
            type="button"
            onClick={() => handleSetExample("https://github.com/cynbit/bitelevate-sample/pull/42")}
            style={{
              fontSize: "0.7rem",
              padding: "0.2rem 0.5rem",
              borderRadius: "var(--radius-sm)",
              backgroundColor: "var(--bg-surface-elevated)",
              border: "1px solid var(--border-subtle)",
              color: "var(--info)",
            }}
          >
            PR #42 (All Rules)
          </button>
          <button
            type="button"
            onClick={() => handleSetExample("https://github.com/cynbit/bitelevate-sample/pull/99")}
            style={{
              fontSize: "0.7rem",
              padding: "0.2rem 0.5rem",
              borderRadius: "var(--radius-sm)",
              backgroundColor: "var(--bg-surface-elevated)",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-muted)",
            }}
          >
            PR #99 (Injection Test)
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.75rem" }}>
        <div style={{ flex: 1, position: "relative" }}>
          <label htmlFor="pr-url-input" style={{ position: "absolute", left: "-9999px" }}>
            GitHub Pull Request URL
          </label>
          <input
            id="pr-url-input"
            type="url"
            placeholder="https://github.com/owner/repository/pull/123"
            value={prUrl}
            onChange={(e) => {
              setPrUrl(e.target.value);
              if (validationError) validateUrl(e.target.value);
            }}
            disabled={createMutation.isPending}
            style={{
              width: "100%",
              padding: "0.7rem 1rem",
              borderRadius: "var(--radius-md)",
              backgroundColor: "var(--bg-base)",
              border: `1px solid ${validationError ? "var(--danger)" : "var(--border-subtle)"}`,
              color: "var(--text-main)",
              fontSize: "0.9rem",
              outline: "none",
            }}
          />
        </div>
        <button
          type="submit"
          id="analyze-pr-button"
          disabled={createMutation.isPending || !prUrl.trim()}
          style={{
            padding: "0.7rem 1.5rem",
            backgroundColor: createMutation.isPending || !prUrl.trim() ? "var(--border-subtle)" : "var(--primary)",
            color: "#ffffff",
            borderRadius: "var(--radius-md)",
            fontWeight: 600,
            fontSize: "0.875rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            cursor: createMutation.isPending || !prUrl.trim() ? "not-allowed" : "pointer",
            boxShadow: createMutation.isPending ? "none" : "0 2px 8px var(--primary-glow)",
            transition: "all 0.15s ease",
          }}
        >
          {createMutation.isPending ? (
            <>
              <span className="animate-pulse" style={{ display: "inline-block" }}>&#x25CF;</span>
              Analyzing PR...
            </>
          ) : (
            "Analyze PR"
          )}
        </button>
      </form>

      {validationError && (
        <div
          role="alert"
          style={{
            marginTop: "0.75rem",
            padding: "0.5rem 0.75rem",
            backgroundColor: "var(--danger-bg)",
            border: "1px solid var(--danger-border)",
            borderRadius: "var(--radius-sm)",
            color: "var(--danger)",
            fontSize: "0.8rem",
          }}
        >
          {validationError}
        </div>
      )}

      {createMutation.isError && (
        <div
          role="alert"
          style={{
            marginTop: "0.75rem",
            padding: "0.5rem 0.75rem",
            backgroundColor: "var(--danger-bg)",
            border: "1px solid var(--danger-border)",
            borderRadius: "var(--radius-sm)",
            color: "var(--danger)",
            fontSize: "0.8rem",
          }}
        >
          {createMutation.error.message}
        </div>
      )}
    </div>
  );
};
