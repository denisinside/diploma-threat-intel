import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { clearSession, getSession } from "@/lib/session";

export function useAuth() {
  const navigate = useNavigate();

  const logout = useCallback(() => {
    clearSession();
    navigate("/login", { replace: true });
  }, [navigate]);

  const session = getSession();

  return {
    isAuthenticated: !!session?.token,
    session,
    logout,
  };
}
