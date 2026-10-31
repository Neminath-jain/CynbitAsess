import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, DecisionRequest, ReviewResponse } from "../api/client";

export function useReviewsList(statusFilter?: string) {
  return useQuery({
    queryKey: ["reviews", statusFilter || "ALL"],
    queryFn: () => api.listReviews(statusFilter),
  });
}

export function useReviewDetail(id: string | undefined) {
  return useQuery({
    queryKey: ["review", id],
    queryFn: () => {
      if (!id) throw new Error("Review ID is required");
      return api.getReview(id);
    },
    enabled: Boolean(id),
  });
}

export function useCreateReviewMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (prUrl: string) => api.createReview(prUrl),
    onSuccess: (data: ReviewResponse) => {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
      queryClient.setQueryData(["review", data.id], data);
    },
  });
}

export function useRecordDecisionMutation(reviewId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      findingId,
      decision,
    }: {
      findingId: string;
      decision: DecisionRequest;
    }) => api.recordDecision(findingId, decision),
    onSuccess: () => {
      if (reviewId) {
        queryClient.invalidateQueries({ queryKey: ["review", reviewId] });
      }
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
    },
  });
}

export function useExportMarkdown(reviewId: string | undefined, enabled = false) {
  return useQuery({
    queryKey: ["review-export", reviewId],
    queryFn: () => {
      if (!reviewId) throw new Error("Review ID required for export");
      return api.exportMarkdown(reviewId);
    },
    enabled: Boolean(reviewId) && enabled,
  });
}
