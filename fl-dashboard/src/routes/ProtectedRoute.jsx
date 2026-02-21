import { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";

export default function ProtectedRoute({ children, allowedRole }) {
  const { role } = useContext(AuthContext);

  if (!role) return <Navigate to="/" />;
  if (role !== allowedRole) return <Navigate to="/" />;

  return children;
}