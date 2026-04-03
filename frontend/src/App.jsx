import React, { useContext } from "react";
import { Navigate, Route, Routes, Link } from "react-router-dom";
import { AuthProvider, AuthContext } from "./auth/AuthContext.jsx";
import { ToastProvider } from "./components/toast/ToastContext.jsx";
import ProtectedRoute from "./routes/ProtectedRoute.jsx";

import LoginPage from "./pages/LoginPage.jsx";
import SignupPage from "./pages/SignupPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import ProjectsPage from "./pages/ProjectsPage.jsx";
import ProjectCreatePage from "./pages/ProjectCreatePage.jsx";
import MatchesPage from "./pages/MatchesPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import NotificationsPage from "./pages/NotificationsPage.jsx";

function AppLayout() {
  const { user, logout } = useContext(AuthContext);

  return (
    <div className="min-h-screen bg-[radial-gradient(1200px_500px_at_10%_0%,rgba(99,102,241,0.22),transparent),radial-gradient(900px_500px_at_90%_10%,rgba(236,72,153,0.14),transparent)]">
      <div className="mx-auto flex max-w-7xl gap-6 px-4 py-6">
        <aside className="hidden w-64 shrink-0 rounded-2xl bg-white/5 ring-1 ring-white/10 p-4 lg:block">
          <div className="mb-4 rounded-xl bg-indigo-600/15 p-4 ring-1 ring-indigo-400/20">
            <div className="text-lg font-bold">Dev Collaboration Finder</div>
            <div className="mt-1 text-sm text-slate-300">
              {user ? `Signed in as ${user.name}` : "Sign in"}
            </div>
          </div>

          <nav className="space-y-2">
            <Link className="block rounded-xl px-3 py-2 text-sm hover:bg-white/5" to="/dashboard">
              Dashboard
            </Link>
            <Link className="block rounded-xl px-3 py-2 text-sm hover:bg-white/5" to="/profile">
              Profile
            </Link>
            <Link className="block rounded-xl px-3 py-2 text-sm hover:bg-white/5" to="/projects">
              Projects
            </Link>
            <Link className="block rounded-xl px-3 py-2 text-sm hover:bg-white/5" to="/matches">
              Match Recommendations
            </Link>
            <Link className="block rounded-xl px-3 py-2 text-sm hover:bg-white/5" to="/chat">
              Chat
            </Link>
            <Link className="block rounded-xl px-3 py-2 text-sm hover:bg-white/5" to="/notifications">
              Notifications
            </Link>

            <div className="mt-4 border-t border-white/10 pt-4">
              <button
                className="w-full rounded-xl bg-white/5 px-3 py-2 text-sm ring-1 ring-white/10 hover:bg-white/10"
                onClick={logout}
              >
                Logout
              </button>
            </div>
          </nav>
        </aside>

        <main className="min-w-0 flex-1">
          <Routes>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/new" element={<ProjectCreatePage />} />
            <Route path="/matches" element={<MatchesPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />

            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/*" element={<AppLayout />} />
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </ToastProvider>
    </AuthProvider>
  );
}

