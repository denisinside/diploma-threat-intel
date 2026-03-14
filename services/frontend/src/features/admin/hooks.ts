import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { adminApi } from "./api";

export function useCompanyRequests() {
  return useQuery({
    queryKey: ["admin", "company-requests"],
    queryFn: adminApi.getCompanyRequests,
  });
}

export function useApproveRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adminApi.approveRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "company-requests"] });
      toast.success("Request approved");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to approve"),
  });
}

export function useRejectRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adminApi.rejectRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "company-requests"] });
      toast.success("Request rejected");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to reject"),
  });
}
