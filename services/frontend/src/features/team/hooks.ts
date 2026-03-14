import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "@/lib/toast";
import { teamApi } from "./api";

export function useCompanyUsers() {
  return useQuery({
    queryKey: ["team", "users"],
    queryFn: teamApi.getUsers,
  });
}

export function useRegisterAnalyst() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: teamApi.registerAnalyst,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", "users"] });
      toast.success("Analyst registered");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to register analyst"),
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: teamApi.deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", "users"] });
      toast.success("User deleted");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to delete user"),
  });
}
