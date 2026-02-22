import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../api/client'
import type {
  GovernanceAccessLog,
  GovernanceIncident,
  GovernanceLineage,
  GovernancePolicy,
} from '../../api/contracts'
import { endpoints } from '../../api/endpoints'

export function useAccessLogs() {
  return useQuery({
    queryKey: ['governance-access-logs'],
    queryFn: () => apiRequest<GovernanceAccessLog[]>(endpoints.governanceAccessLogs),
  })
}

export function useLineage() {
  return useQuery({
    queryKey: ['governance-lineage'],
    queryFn: () => apiRequest<GovernanceLineage>(endpoints.governanceLineage),
  })
}

export function usePolicies() {
  return useQuery({
    queryKey: ['governance-policies'],
    queryFn: () => apiRequest<GovernancePolicy[]>(endpoints.governancePolicies),
  })
}

export function useIncidents() {
  return useQuery({
    queryKey: ['governance-incidents'],
    queryFn: () => apiRequest<GovernanceIncident[]>(endpoints.governanceIncidents),
  })
}
