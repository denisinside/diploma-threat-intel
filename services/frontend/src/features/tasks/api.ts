import { apiClient } from "@/lib/api";

export const tasksApi = {
  triggerScan: () => apiClient.post<{ message: string }>("/tasks/scan/trigger"),
  getScanStatus: () =>
    apiClient.get<{ status: string; message: string; last_processed_commit: string | null }>(
      "/tasks/scan/status"
    ),
};
