import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { subscriptionsApi } from "./api";

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
    },
  });
}

export function useCreateChannel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: subscriptionsApi.createChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
    },
  });
}

export function useUpdateChannel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ channelId, payload }: { channelId: string; payload: Parameters<typeof subscriptionsApi.updateChannel>[1] }) =>
      subscriptionsApi.updateChannel(channelId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
    },
  });
}
