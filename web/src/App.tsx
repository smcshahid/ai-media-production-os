import { Navigate, Route, Routes } from "react-router-dom";

import { RequireAuth } from "./components/RequireAuth";
import { AppShell } from "./components/layout/AppShell";
import { AssetsPage } from "./routes/AssetsPage";
import { AuditPage } from "./routes/AuditPage";
import { DashboardPage } from "./routes/DashboardPage";
import { ExportPage } from "./routes/ExportPage";
import { HistoryPage } from "./routes/HistoryPage";
import { LineagePage } from "./routes/LineagePage";
import { LoginPage } from "./routes/LoginPage";
import { ReviewPage } from "./routes/ReviewPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/assets" element={<AssetsPage />} />
        <Route path="/export" element={<ExportPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/lineage" element={<LineagePage />} />
        <Route path="/audit" element={<AuditPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
