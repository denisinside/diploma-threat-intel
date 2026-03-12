import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { subscriptionsApi } from "./api";
import { toast } from "@/lib/toast";

export function useSubscriptions(companyId?: string) {
  return useQuery({
    queryKey: ["subscriptions", companyId],
    queryFn: () => subscriptionsApi.getCompanySubscriptions(companyId as string),
    enabled: Boolean(companyId),
  });
}

export function useNotificationChannels(companyId?: string) {
  return useQuery({
    queryKey: ["channels", companyId],
    queryFn: () => subscriptionsApi.getCompanyChannels(companyId as string),
    enabled: Boolean(companyId),
  });
}

export function useCreateSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: subscriptionsApi.createSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      toast.success("Subscription created");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to create subscription"),
  });
}

export function useCreateChannel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: subscriptionsApi.createChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
      toast.success("Channel created");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to create channel"),
  });
}

export function useUpdateChannel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ channelId, payload }: { channelId: string; payload: Parameters<typeof subscriptionsApi.updateChannel>[1] }) =>
      subscriptionsApi.updateChannel(channelId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
      toast.success("Channel updated");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to update channel"),
  });
}

export function useDeleteChannel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: subscriptionsApi.deleteChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
      toast.success("Channel deleted");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to delete channel"),
  });
}

export function useDeleteSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: subscriptionsApi.deleteSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      toast.success("Subscription deleted");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to delete subscription"),
  });
}

export function useUpdateSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ subId, payload }: { subId: string; payload: { keyword?: string; min_severity?: "critical" | "high" | "medium" | "low" | "unknown" } }) =>
      subscriptionsApi.updateSubscription(subId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      toast.success("Subscription updated");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to update subscription"),
  });
}

export function useTestChannel() {
  return useMutation({
    mutationFn: subscriptionsApi.testChannel,
    onSuccess: () => toast.success("Test notification sent"),
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to send test"),
  });
}
