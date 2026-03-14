import { useAuth } from "./useAuth";

export type Role = "super_admin" | "admin" | "analyst" | "viewer";

/** Returns true if current user has at least one of the allowed roles */
export function useRoleGuard(allowedRoles: Role[]): boolean {
  const { session } = useAuth();
  const role = session?.user?.role;
  if (!role) return false;
  return allowedRoles.includes(role);
}

/** Returns true if user can create/edit/delete assets and subscriptions (admin only) */
export function useCanMutate(): boolean {
  return useRoleGuard(["admin"]);
}

/** Returns true if user can create/update tickets (admin or analyst) */
export function useCanManageTickets(): boolean {
  return useRoleGuard(["admin", "analyst"]);
}

/** Returns true only for company admin */
export function useIsAdmin(): boolean {
  return useRoleGuard(["admin"]);
}

/** Returns true only for super_admin (system admin) */
export function useIsSuperAdmin(): boolean {
  return useRoleGuard(["super_admin"]);
}
