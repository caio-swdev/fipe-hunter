import { Navigate } from 'react-router-dom'
import { useAdminAuthStore } from '../store/adminAuth'

interface AdminGuardProps {
  children: React.ReactNode
}

export function AdminGuard({ children }: AdminGuardProps) {
  const token = useAdminAuthStore((s) => s.token)
  if (!token) return <Navigate to="/admin/login" replace />
  return <>{children}</>
}
