import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { DataTable } from '../../components/common/DataTable'
import { StatusBadge } from '../../components/common/StatusBadge'
import type { ProductSummary } from '../../api/contracts'
import { useProducts } from '../../features/products/useProducts'

export function ProductsPage() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useProducts()

  const rows = useMemo(() => data ?? [], [data])

  if (isLoading) {
    return <p>Loading products...</p>
  }

  if (isError) {
    return <p>Unable to load products.</p>
  }

  return (
    <section>
      <h1>Products</h1>
      <DataTable<ProductSummary>
        rows={rows}
        emptyText="No products found"
        columns={[
          { key: 'name', header: 'Name', render: (row) => row.display_name },
          { key: 'owner', header: 'Owner Team', render: (row) => row.owner_team },
          { key: 'env', header: 'Environment', render: (row) => row.environment },
          { key: 'health', header: 'Health', render: (row) => <StatusBadge status={row.health_status} /> },
          {
            key: 'actions',
            header: 'Actions',
            render: (row) => (
              <button type="button" onClick={() => navigate(`/products/${row.id}`)}>
                View detail
              </button>
            ),
          },
        ]}
      />
    </section>
  )
}
