import type { components } from "./schema";

export type ReviewResponse = components["schemas"]["ReviewResponse"];
export type ReviewListItemResponse = components["schemas"]["ReviewListItemResponse"];
export type FindingResponse = components["schemas"]["FindingResponse"];
export type DecisionResponse = components["schemas"]["DecisionResponse"];
export type DecisionRequest = components["schemas"]["DecisionRequest"];
export type ReviewCreateRequest = components["schemas"]["ReviewCreateRequest"];

const MENTOR_TOKEN_KEY = "bitelevate_mentor_token";
const DEFAULT_MENTOR_TOKEN = "test-mentor-token";

export function getMentorToken(): string {
  if (typeof window !== "undefined" && window.localStorage) {
    const stored = localStorage.getItem(MENTOR_TOKEN_KEY);
    if (stored && stored !== "dev-mentor-token-xyz" && stored !== "secret") {
      return stored;
    }
    return DEFAULT_MENTOR_TOKEN;
  }
  return DEFAULT_MENTOR_TOKEN;
}

export function setMentorToken(token: string): void {
  if (typeof window !== "undefined" && window.localStorage) {
    localStorage.setItem(MENTOR_TOKEN_KEY, token);
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  headers.set("X-Mentor-Token", getMentorToken());

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `API Error ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.message) {
        errorMessage = errJson.message;
      } else if (errJson && errJson.detail) {
        errorMessage = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMessage);
  }

  // Handle empty or text responses (like Markdown export)
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

export const api = {
  listReviews: async (statusFilter?: string): Promise<ReviewListItemResponse[]> => {
    const url = statusFilter
      ? `/api/v1/reviews?status=${encodeURIComponent(statusFilter)}`
      : "/api/v1/reviews";
    return request<ReviewListItemResponse[]>(url);
  },

  getReview: async (id: string): Promise<ReviewResponse> => {
    return request<ReviewResponse>(`/api/v1/reviews/${id}`);
  },

  createReview: async (prUrl: string): Promise<ReviewResponse> => {
    return request<ReviewResponse>("/api/v1/reviews", {
      method: "POST",
      body: JSON.stringify({ pr_url: prUrl } satisfies ReviewCreateRequest),
    });
  },

  recordDecision: async (
    findingId: string,
    decision: DecisionRequest
  ): Promise<DecisionResponse> => {
    return request<DecisionResponse>(`/api/v1/findings/${findingId}/decision`, {
      method: "POST",
      body: JSON.stringify(decision),
    });
  },

  exportMarkdown: async (reviewId: string): Promise<string> => {
    return request<string>(`/api/v1/reviews/${reviewId}/export`);
  },
};
