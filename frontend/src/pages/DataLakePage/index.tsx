import { useEffect, useMemo, useState } from 'react'
import { DataTable } from '../../components/common/DataTable'
import type { DataLakeDatasetSummary } from '../../api/contracts'
import {
  useDatasetDetail,
  useDatasetQuality,
  useDatasets,
} from '../../features/datalake/useDataLake'

export function DataLakePage() {
  const { data, isLoading, isError } = useDatasets()
  const [selectedDatasetId, setSelectedDatasetId] = useState('')

  useEffect(() => {
    if (!selectedDatasetId && data && data.length > 0) {
      setSelectedDatasetId(data[0].id)
    }
  }, [selectedDatasetId, data])

  const rows = useMemo(() => data ?? [], [data])
  const detail = useDatasetDetail(selectedDatasetId)
  const quality = useDatasetQuality(selectedDatasetId)

  if (isLoading) {
    return <p>Loading datasets...</p>
  }

  if (isError) {
    return <p>Unable to load datasets.</p>
  }

  return (
    <section>
      <h1>Data Lake</h1>
      <DataTable<DataLakeDatasetSummary>
        rows={rows}
        emptyText="No datasets found"
        columns={[
          { key: 'dataset', header: 'Dataset', render: (row) => row.id },
          { key: 'product', header: 'Product', render: (row) => row.product_id },
          { key: 'layer', header: 'Layer', render: (row) => row.layer },
          { key: 'table', header: 'Table', render: (row) => row.table_name },
          {
            key: 'freshness',
            header: 'Freshness',
            render: (row) => `${row.freshness_seconds}s`,
          },
          {
            key: 'actions',
            header: 'Actions',
            render: (row) => (
              <button type="button" onClick={() => setSelectedDatasetId(row.id)}>
                Inspect
              </button>
            ),
          },
        ]}
      />

      <div className="details-grid">
        <article className="product-card">
          <h2>Metadata</h2>
          {!selectedDatasetId ? <p>Select a dataset to view metadata.</p> : null}
          {detail.isLoading ? <p>Loading metadata...</p> : null}
          {detail.isError ? <p>Unable to load metadata.</p> : null}
          {detail.data ? (
            <>
              <p>Dataset: {detail.data.id}</p>
              <p>Product: {detail.data.product_id}</p>
              <p>Layer: {detail.data.layer}</p>
              <p>Table: {detail.data.table_name}</p>
              <p>Schema version: {detail.data.schema_version}</p>
            </>
          ) : null}
        </article>

        <article className="product-card">
          <h2>Quality</h2>
          {!selectedDatasetId ? <p>Select a dataset to view quality.</p> : null}
          {quality.isLoading ? <p>Loading quality...</p> : null}
          {quality.isError ? <p>Unable to load quality data.</p> : null}
          {quality.data ? (
            <>
              <p>Score: {quality.data.quality_score}%</p>
              <p>Checks passed: {quality.data.checks_passed}</p>
              <p>Checks failed: {quality.data.checks_failed}</p>
            </>
          ) : null}
        </article>
      </div>
    </section>
  )
}
