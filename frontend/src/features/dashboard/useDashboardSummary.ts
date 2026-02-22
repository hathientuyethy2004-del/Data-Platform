import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../api/client'
import type { DashboardSummary } from '../../api/contracts'
import { endpoints } from '../../api/endpoints'

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => apiRequest<DashboardSummary>(endpoints.dashboardSummary),
  })
}
