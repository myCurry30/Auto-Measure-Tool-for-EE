import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import AppLayout from "./layouts/AppLayout";
import LoginPage from "./pages/LoginPage";
import ConnectPage from "./pages/ConnectPage";

// Placeholder pages for routes not yet implemented
const Placeholder = ({ title }: { title: string }) => (
  <div style={{ padding: 40, textAlign: "center" }}>
    <h2>{title}</h2>
    <p>Under development...</p>
  </div>
);

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route
                path="/connect"
                element={<ConnectPage />}
              />
              <Route
                path="/config"
                element={<Placeholder title="Config" />}
              />
              <Route
                path="/measure"
                element={<Placeholder title="Measure" />}
              />
              <Route
                path="/help"
                element={<Placeholder title="Manual" />}
              />
            </Route>
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  );
}
