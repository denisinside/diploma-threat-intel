import { apiClient } from "@/lib/api";
import type { Ticket, TicketStatus } from "@/types";

export const ticketsApi = {
  getCompanyTickets: (companyId: string, status?: TicketStatus) => {
    const params = new URLSearchParams({ company_id: companyId, limit: "300" });
    if (status) params.set("status", status);
    return apiClient.get<Ticket[]>(`/tickets?${params}`);
  },
  countTickets: (companyId: string, status?: TicketStatus) => {
    const params = new URLSearchParams({ company_id: companyId });
    if (status) params.set("status", status);
    return apiClient.get<{ company_id: string; status?: string; count: number }>(
      `/tickets/count?${params}`
    );
  },
  createTicket: (payload: {
    company_id: string;
    asset_id: string;
    vulnerability_id: string;
    priority?: Ticket["priority"];
    notes?: string;
  }) => apiClient.post<Ticket>("/tickets", payload),
  updateTicket: (ticketId: string, payload: Partial<Pick<Ticket, "status" | "priority" | "notes">>) =>
    apiClient.put<Ticket>(`/tickets/${ticketId}`, payload),
};
