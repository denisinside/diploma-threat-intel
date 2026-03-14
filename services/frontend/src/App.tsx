import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterCompanyRequestPage } from "@/pages/auth/RegisterCompanyRequestPage";
import { AdminCompanyRequestsPage } from "@/pages/AdminCompanyRequestsPage";
import { TeamPage } from "@/pages/TeamPage";
import { OverviewPage } from "@/pages/OverviewPage";
import { AssetsPage } from "@/pages/AssetsPage";
import { LeaksPage } from "@/pages/LeaksPage";
import { VulnerabilitiesPage } from "@/pages/VulnerabilitiesPage";
import { VulnerabilityDetailPage } from "@/pages/VulnerabilityDetailPage";
import { TicketsPage } from "@/pages/TicketsPage";
import { SubscriptionsPage } from "@/pages/SubscriptionsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { useAuth } from "@/hooks/useAuth";

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register-company-request" element={<RegisterCompanyRequestPage />} />
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <Layout />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      >
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="overview" element={<OverviewPage />} />
        <Route path="assets" element={<AssetsPage />} />
        <Route path="leaks" element={<LeaksPage />} />
        <Route path="vulnerabilities/:id" element={<VulnerabilityDetailPage />} />
        <Route path="vulnerabilities" element={<VulnerabilitiesPage />} />
        <Route path="tickets" element={<TicketsPage />} />
        <Route path="subscriptions" element={<SubscriptionsPage />} />
        <Route path="team" element={<TeamPage />} />
        <Route path="admin/company-requests" element={<AdminCompanyRequestsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
