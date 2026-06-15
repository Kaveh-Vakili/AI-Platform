import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

const isAuth = () => !!localStorage.getItem("token");

export default function PrivateRoute({ children }: { children: ReactNode }) {
  return isAuth() ? <>{children}</> : <Navigate to="/login" />;
}
