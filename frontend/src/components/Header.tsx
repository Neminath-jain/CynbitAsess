import React, { useState } from "react";
import { Link } from "react-router-dom";
import { getMentorToken, setMentorToken } from "../api/client";

export const Header: React.FC = () => {
  const [token, setTokenState] = useState(getMentorToken());
  const [isEditingToken, setIsEditingToken] = useState(false);
  const [tempToken, setTempToken] = useState(token);

  const handleSaveToken = (e: React.FormEvent) => {
    e.preventDefault();
    setMentorToken(tempToken);
    setTokenState(tempToken);
    setIsEditingToken(false);
  };

  return (
    <header
      style={{
        backgroundColor: "var(--bg-surface)",
        borderBottom: "1px solid var(--border-subtle)",
        padding: "0.75rem 1.5rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <Link
          to="/"
          style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
          aria-label="BitElevate PR Review Copilot Home"
        >
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "var(--radius-md)",
              backgroundColor: "var(--primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 12px var(--primary-glow)",
              color: "#ffffff",
              fontWeight: 700,
              fontSize: "1.2rem",
            }}
          >
            BE
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "1rem", letterSpacing: "-0.01em", color: "var(--text-main)" }}>
              BitElevate PR Review Copilot
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Cynbit Technologies &bull; Mentor Triage Console
            </div>
          </div>
        </Link>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <nav style={{ display: "flex", gap: "0.5rem" }}>
          <Link
            to="/"
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-md)",
              fontSize: "0.875rem",
              fontWeight: 500,
              color: "var(--text-main)",
              backgroundColor: "var(--bg-surface-elevated)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            Review Queue
          </Link>
        </nav>

        <div style={{ position: "relative" }}>
          <button
            onClick={() => setIsEditingToken(!isEditingToken)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.4rem 0.75rem",
              borderRadius: "var(--radius-md)",
              fontSize: "0.75rem",
              backgroundColor: "rgba(16, 185, 129, 0.1)",
              border: "1px solid var(--success-border)",
              color: "var(--success)",
              fontWeight: 500,
            }}
            title="Click to configure Mentor Authentication Token"
            aria-label="Configure Mentor Token"
          >
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: "var(--success)",
              }}
            />
            Mentor Auth: Active
          </button>

          {isEditingToken && (
            <div
              style={{
                position: "absolute",
                right: 0,
                top: "120%",
                width: "320px",
                backgroundColor: "var(--bg-surface-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-lg)",
                padding: "1rem",
                boxShadow: "var(--shadow-lg)",
                zIndex: 50,
              }}
            >
              <form onSubmit={handleSaveToken}>
                <label
                  htmlFor="mentor-token-input"
                  style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.5rem" }}
                >
                  Configure X-Mentor-Token Header
                </label>
                <input
                  id="mentor-token-input"
                  type="text"
                  value={tempToken}
                  onChange={(e) => setTempToken(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    borderRadius: "var(--radius-sm)",
                    backgroundColor: "var(--bg-base)",
                    border: "1px solid var(--border-subtle)",
                    color: "var(--text-main)",
                    fontSize: "0.85rem",
                    fontFamily: "var(--font-mono)",
                    marginBottom: "0.75rem",
                  }}
                />
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
                  <button
                    type="button"
                    onClick={() => setIsEditingToken(false)}
                    style={{
                      padding: "0.3rem 0.6rem",
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      padding: "0.3rem 0.75rem",
                      fontSize: "0.75rem",
                      backgroundColor: "var(--primary)",
                      color: "#fff",
                      borderRadius: "var(--radius-sm)",
                      fontWeight: 600,
                    }}
                  >
                    Save Token
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
