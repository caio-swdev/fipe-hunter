import { useQuery } from '@tanstack/react-query'
import { fetchAdminHealth } from '../services/api'
import { useAdminAuthStore } from '../store/adminAuth'

export function useAdminHealth() {
  const token = useAdminAuthStore((s) => s.token)
  return useQuery({
    queryKey: ['admin-health'],
    queryFn: () => fetchAdminHealth(token!),
    refetchInterval: 30_000,
    enabled: !!token,
  })
}
