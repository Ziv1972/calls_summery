import React from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import { AppLayout } from "./components/Layout/AppLayout";
import { LoginScreen } from "./screens/LoginScreen";
import { DashboardScreen } from "./screens/DashboardScreen";
import { CallsScreen } from "./screens/CallsScreen";
import { CallDetailScreen } from "./screens/CallDetailScreen";
import { ChatScreen } from "./screens/ChatScreen";
import { ContactsScreen } from "./screens/ContactsScreen";
import { UploadScreen } from "./screens/UploadScreen";
import { SettingsScreen } from "./screens/SettingsScreen";

/** Error boundary to catch React rendering crashes. */
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
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 max-w-xl mx-auto mt-20">
          <h1 className="text-xl font-bold text-red-600 mb-3">Something went wrong</h1>
          <pre className="text-sm bg-red-50 p-4 rounded-lg overflow-auto whitespace-pre-wrap text-red-800">
            {this.state.error?.message}
            {"\n"}
            {this.state.error?.stack}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg"
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  );
}

export function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginScreen />} />
          <Route element={<ProtectedRoute />}>
            <Route index element={<DashboardScreen />} />
            <Route path="calls" element={<CallsScreen />} />
            <Route path="calls/:callId" element={<CallDetailScreen />} />
            <Route path="chat" element={<ChatScreen />} />
            <Route path="contacts" element={<ContactsScreen />} />
            <Route path="upload" element={<UploadScreen />} />
            <Route path="settings" element={<SettingsScreen />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
