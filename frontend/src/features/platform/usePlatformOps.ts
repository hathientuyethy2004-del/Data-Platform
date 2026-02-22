import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../api/client'
import type {
  PlatformActionResult,
  PlatformExecution,
  PlatformService,
  PlatformStatus,
} from '../../api/contracts'
import { endpoints } from '../../api/endpoints'

export function usePlatformStatus() {
  return useQuery({
    queryKey: ['platform-status'],
    queryFn: () => apiRequest<PlatformStatus>(endpoints.platformStatus),
  })
}

export function usePlatformServices() {
  return useQuery({
    queryKey: ['platform-services'],
    queryFn: () => apiRequest<PlatformService[]>(endpoints.platformServices),
  })
}

export function usePlatformExecutions() {
  return useQuery({
    queryKey: ['platform-executions'],
    queryFn: () => apiRequest<PlatformExecution[]>(endpoints.platformExecutions),
  })
}

export function useRunPlatformAction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (action: string) =>
      apiRequest<PlatformActionResult>(endpoints.platformActionRun(action), { method: 'POST' }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['platform-status'] })
      await queryClient.invalidateQueries({ queryKey: ['platform-executions'] })
    },
  })
}
