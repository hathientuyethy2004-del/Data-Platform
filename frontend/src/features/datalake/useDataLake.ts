import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../api/client'
import type {
  DataLakeDatasetDetail,
  DataLakeDatasetQuality,
  DataLakeDatasetSummary,
} from '../../api/contracts'
import { endpoints } from '../../api/endpoints'

export function useDatasets() {
  return useQuery({
    queryKey: ['datalake-datasets'],
    queryFn: () => apiRequest<DataLakeDatasetSummary[]>(endpoints.datalakeDatasets),
  })
}

export function useDatasetDetail(datasetId: string) {
  return useQuery({
    queryKey: ['datalake-dataset-detail', datasetId],
    queryFn: () => apiRequest<DataLakeDatasetDetail>(endpoints.datalakeDatasetDetail(datasetId)),
    enabled: Boolean(datasetId),
  })
}

export function useDatasetQuality(datasetId: string) {
  return useQuery({
    queryKey: ['datalake-dataset-quality', datasetId],
    queryFn: () => apiRequest<DataLakeDatasetQuality>(endpoints.datalakeDatasetQuality(datasetId)),
    enabled: Boolean(datasetId),
  })
}
