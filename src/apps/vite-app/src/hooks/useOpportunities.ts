import { useQuery } from '@tanstack/react-query'
import { fetchOpportunities, fetchDashboardSummary } from '../services/api'

export function useOpportunities() {
  return useQuery({
    queryKey: ['opportunities'],
    queryFn: fetchOpportunities,
    refetchInterval: 60000,
  })
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
    refetchInterval: 60000,
  })
}
