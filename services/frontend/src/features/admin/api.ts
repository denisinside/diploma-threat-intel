import { apiClient } from "@/lib/api";

export type CompanyRequest = {
  _id: string;
  name: string;
  domain: string;
  admin_email: string;
  admin_full_name: string;
  status: string;
  created_at?: string;
};

export const adminApi = {
  getCompanyRequests: () => apiClient.get<CompanyRequest[]>("/admin/company-requests"),
  approveRequest: (requestId: string) =>
    apiClient.post<{ company: unknown; admin_user: unknown }>(`/admin/company-requests/${requestId}/approve`),
  rejectRequest: (requestId: string) =>
    apiClient.post<{ message: string }>(`/admin/company-requests/${requestId}/reject`),
};
