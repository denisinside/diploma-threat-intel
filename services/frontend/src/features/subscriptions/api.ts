import { apiClient } from "@/lib/api";
import type {
  ChannelType,
  NotificationChannel,
  NotificationChannelConfig,
  Severity,
  Subscription,
} from "@/types";

export const subscriptionsApi = {
  getCompanySubscriptions: (companyId: string) =>
    apiClient.get<Subscription[]>(
      `/subscriptions?company_id=${encodeURIComponent(companyId)}&limit=300`
    ),
  getCompanyChannels: (companyId: string) =>
    apiClient.get<NotificationChannel[]>(
      `/subscriptions/channels?company_id=${encodeURIComponent(companyId)}&limit=300`
    ),
  createSubscription: (payload: {
    company_id: string;
    sub_type: "vulnerability" | "leak";
    keyword: string;
    min_severity?: "critical" | "high" | "medium" | "low" | "unknown";
  }) => apiClient.post<Subscription>("/subscriptions", payload),
  createChannel: (payload: {
    company_id: string;
    name: string;
    channel_type: ChannelType;
    config: NotificationChannelConfig;
  }) => apiClient.post<NotificationChannel>("/subscriptions/channels", payload),
  updateChannel: (channelId: string, payload: Partial<NotificationChannel>) =>
    apiClient.put<NotificationChannel>(`/subscriptions/channels/${channelId}`, payload),
  deleteChannel: (channelId: string) =>
    apiClient.delete<{ message: string }>(`/subscriptions/channels/${channelId}`),
  deleteSubscription: (subId: string) =>
    apiClient.delete<{ message: string }>(`/subscriptions/rules/${subId}`),
  updateSubscription: (subId: string, payload: { keyword?: string; min_severity?: Severity }) =>
    apiClient.put<Subscription>(`/subscriptions/rules/${subId}`, payload),
  testChannel: (channelId: string) =>
    apiClient.post<{ message: string }>(`/subscriptions/channels/${channelId}/test`),
};
