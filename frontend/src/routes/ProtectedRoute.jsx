import React, { useContext } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { AuthContext } from "../auth/AuthContext.jsx";

export default function ProtectedRoute({ redirectTo = "/login" }) {
  const { accessToken, authLoading } = useContext(AuthContext);
  if (authLoading) return <div className="p-6 text-slate-200">Loading...</div>;
  if (!accessToken) return <Navigate to={redirectTo} replace />;
  return <Outlet />;
}

