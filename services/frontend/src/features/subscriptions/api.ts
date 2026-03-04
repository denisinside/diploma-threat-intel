import { apiClient } from "@/lib/api";
import type { NotificationChannel, Subscription } from "@/types";

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
    channel_type: "email" | "telegram" | "slack" | "discord" | "webhook";
    config: Record<string, unknown>;
  }) => apiClient.post<NotificationChannel>("/subscriptions/channels", payload),
  updateChannel: (channelId: string, payload: Partial<NotificationChannel>) =>
    apiClient.put<NotificationChannel>(`/subscriptions/channels/${channelId}`, payload),
};
