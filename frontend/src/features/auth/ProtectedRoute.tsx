import { Navigate } from "react-router-dom"
import { useAuth } from "./AuthContext"
import type { ReactNode } from "react"

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) return null
  if (!user) return <Navigate to="/login" />

  return children
}