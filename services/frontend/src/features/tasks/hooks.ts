import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { tasksApi } from "./api";

export function useScanStatus() {
  return useQuery({
    queryKey: ["scan-status"],
    queryFn: tasksApi.getScanStatus,
    refetchInterval: 30_000,
  });
}

export function useTriggerScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: tasksApi.triggerScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scan-status"] });
      toast.success("Scan triggered");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to trigger scan"),
  });
}
