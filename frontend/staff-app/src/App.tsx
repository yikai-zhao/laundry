import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/auth";
import Navbar from "./components/Navbar";
import LoginPage from "./pages/LoginPage";
import OrderListPage from "./pages/OrderListPage";
import NewOrderPage from "./pages/NewOrderPage";
import OrderDetailPage from "./pages/OrderDetailPage";
import ReceiptPage from "./pages/ReceiptPage";
import InspectionReportPage from "./pages/InspectionReportPage";
import AdminPage from "./pages/AdminPage";
import React from "react";

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("[ErrorBoundary] Caught error:", error);
    console.error("[ErrorBoundary] Error info:", errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ color: "red", padding: "20px", fontFamily: "sans-serif" }}>
          <h1>Application Error</h1>
          <p>{this.state.error?.message}</p>
          <p>Please check the browser console for more details.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return (
    <>
      <Navbar />
      {children}
    </>
  );
}

export default function App() {
  console.log("[App] Initializing routes and auth check");
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/orders" element={<ProtectedRoute><OrderListPage /></ProtectedRoute>} />
          <Route path="/orders/new" element={<ProtectedRoute><NewOrderPage /></ProtectedRoute>} />
          <Route path="/orders/:id" element={<ProtectedRoute><OrderDetailPage /></ProtectedRoute>} />
          <Route path="/orders/:id/receipt" element={<ProtectedRoute><ReceiptPage /></ProtectedRoute>} />
          <Route path="/orders/:id/report" element={<ProtectedRoute><InspectionReportPage /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/orders" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
