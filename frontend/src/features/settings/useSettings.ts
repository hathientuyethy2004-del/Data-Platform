import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../api/client'
import type { PreferencesUpdate, UserPreferences, UserProfile } from '../../api/contracts'
import { endpoints } from '../../api/endpoints'

export function useProfile() {
  return useQuery({
    queryKey: ['me-profile'],
    queryFn: () => apiRequest<UserProfile>(endpoints.meProfile),
  })
}

export function usePreferences() {
  return useQuery({
    queryKey: ['me-preferences'],
    queryFn: () => apiRequest<UserPreferences>(endpoints.mePreferences),
  })
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: PreferencesUpdate) =>
      apiRequest<UserPreferences>(endpoints.mePreferences, { method: 'PATCH', body: payload }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['me-preferences'] })
    },
  })
}
