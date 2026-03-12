import { useAuth } from "./useAuth";

export type Role = "admin" | "analyst" | "viewer";

/** Returns true if current user has at least one of the allowed roles */
export function useRoleGuard(allowedRoles: Role[]): boolean {
  const { session } = useAuth();
  const role = session?.user?.role;
  if (!role) return false;
  return allowedRoles.includes(role);
}

/** Returns true if user can create/edit/delete (admin or analyst) */
export function useCanMutate(): boolean {
  return useRoleGuard(["admin", "analyst"]);
}

/** Returns true only for admin */
export function useIsAdmin(): boolean {
  return useRoleGuard(["admin"]);
}
