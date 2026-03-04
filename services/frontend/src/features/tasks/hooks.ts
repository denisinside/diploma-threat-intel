import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
    },
  });
}
