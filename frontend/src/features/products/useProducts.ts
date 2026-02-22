import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../api/client'
import type { ProductDetail, ProductSummary } from '../../api/contracts'
import { endpoints } from '../../api/endpoints'

export function useProducts() {
  return useQuery({
    queryKey: ['products'],
    queryFn: () => apiRequest<ProductSummary[]>(endpoints.products),
  })
}

export function useProductDetail(productId: string) {
  return useQuery({
    queryKey: ['product-detail', productId],
    queryFn: () => apiRequest<ProductDetail>(endpoints.productDetail(productId)),
    enabled: Boolean(productId),
  })
}

export function useRunProductAction(productId: string, action: 'test' | 'demo') {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => {
      const url = action === 'test' ? endpoints.productTestsRun(productId) : endpoints.productDemosRun(productId)
      return apiRequest<{ execution_id: string; status: string }>(url, { method: 'POST' })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['products'] })
      await queryClient.invalidateQueries({ queryKey: ['product-detail', productId] })
    },
  })
}
