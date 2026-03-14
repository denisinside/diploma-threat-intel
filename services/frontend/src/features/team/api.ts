import { apiClient } from "@/lib/api";

export const teamApi = {
  getUsers: () => apiClient.get<Array<{ _id: string; email: string; full_name: string; role: string }>>("/team/users"),
  registerAnalyst: (data: { email: string; full_name: string; password: string }) =>
    apiClient.post<{ _id: string; email: string; full_name: string; role: string }>("/team/analysts", data),
  deleteUser: (userId: string) => apiClient.delete(`/team/users/${userId}`),
};
