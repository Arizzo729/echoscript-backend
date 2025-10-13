// components/PrivateRoute.jsx
import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function PrivateRoute() {
  const { user, loading } = useAuth();

  // Still checking session? show nothing (or a spinner)
  if (loading) return null;

  // Not logged in → redirect
  if (!user) return <Navigate to="/signin" replace />;

  // Logged in → render child routes
  return <Outlet />;
}
