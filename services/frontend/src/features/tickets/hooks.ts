import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { TicketStatus } from "@/types";
import { ticketsApi } from "./api";

export function useTickets(companyId?: string, status?: TicketStatus) {
  return useQuery({
    queryKey: ["tickets", companyId, status ?? "all"],
    queryFn: () => ticketsApi.getCompanyTickets(companyId as string, status),
    enabled: Boolean(companyId),
  });
}

export function useTicketCount(companyId?: string, status?: TicketStatus) {
  return useQuery({
    queryKey: ["tickets-count", companyId, status ?? "all"],
    queryFn: () => ticketsApi.countTickets(companyId as string, status),
    enabled: Boolean(companyId),
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ticketsApi.createTicket,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["tickets-count"] });
    },
  });
}

export function useUpdateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ticketId, payload }: { ticketId: string; payload: Parameters<typeof ticketsApi.updateTicket>[1] }) =>
      ticketsApi.updateTicket(ticketId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["tickets-count"] });
    },
  });
}
