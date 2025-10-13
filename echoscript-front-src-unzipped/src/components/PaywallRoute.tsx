// components/PaywallRoute.tsx
import { Navigate, Outlet } from "react-router-dom";

export function PaywallRoute({ isActive }: { isActive: boolean }) {
  return isActive ? <Outlet /> : <Navigate to="/purchase" replace />;
}
