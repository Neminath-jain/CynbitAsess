import React from "react";
import { Link } from "react-router-dom";

export const NotFoundPage: React.FC = () => {
  return (
    <main
      style={{
        maxWidth: "600px",
        margin: "5rem auto",
        textAlign: "center",
        padding: "2rem",
        backgroundColor: "var(--bg-surface)",
        borderRadius: "var(--radius-xl)",
        border: "1px solid var(--border-subtle)",
      }}
    >
      <div style={{ fontSize: "3rem", marginBottom: "1rem", color: "var(--text-dim)" }}>
        404
      </div>
      <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.5rem" }}>
        Page Not Found
      </h1>
      <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: "1.5rem" }}>
        The page or review session you requested does not exist.
      </p>
      <Link
        to="/"
        style={{
          padding: "0.6rem 1.25rem",
          backgroundColor: "var(--primary)",
          color: "#ffffff",
          borderRadius: "var(--radius-md)",
          fontWeight: 600,
          fontSize: "0.85rem",
        }}
      >
        &larr; Return to Review Queue
      </Link>
    </main>
  );
};
