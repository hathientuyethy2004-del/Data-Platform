import { useParams } from 'react-router-dom'
import { StatusBadge } from '../../components/common/StatusBadge'
import { useProductDetail, useRunProductAction } from '../../features/products/useProducts'
import { useAuth } from '../../app/providers/AuthProvider'

export function ProductDetailPage() {
  const { productId = '' } = useParams()
  const { role, canOperate } = useAuth()
  const { data, isLoading, isError } = useProductDetail(productId)
  const runTest = useRunProductAction(productId, 'test')
  const runDemo = useRunProductAction(productId, 'demo')

  if (isLoading) {
    return <p>Loading product detail...</p>
  }

  if (isError || !data) {
    return <p>Unable to load product detail.</p>
  }

  return (
    <section>
      <h1>{data.display_name}</h1>
      <StatusBadge status={data.health_status} />
      <p>{data.description}</p>
      <p>Owner team: {data.owner_team}</p>
      <p>Environment: {data.environment}</p>
      <p>SLA target: {data.sla_target_pct}%</p>

      <div className="actions-row">
        <button
          type="button"
          onClick={() => runTest.mutate()}
          disabled={runTest.isPending || !canOperate}
          title={canOperate ? 'Run product tests' : `Role ${role ?? 'anonymous'} cannot run tests`}
        >
          {runTest.isPending ? 'Running test...' : 'Run test'}
        </button>
        <button
          type="button"
          onClick={() => runDemo.mutate()}
          disabled={runDemo.isPending || !canOperate}
          title={canOperate ? 'Run product demo' : `Role ${role ?? 'anonymous'} cannot run demo`}
        >
          {runDemo.isPending ? 'Running demo...' : 'Run demo'}
        </button>
      </div>
    </section>
  )
}
