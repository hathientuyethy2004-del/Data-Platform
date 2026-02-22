import { KpiCard } from '../../components/common/KpiCard'
import { StatusBadge } from '../../components/common/StatusBadge'
import { useDashboardSummary } from '../../features/dashboard/useDashboardSummary'

export function DashboardPage() {
  const { data, isLoading, isError } = useDashboardSummary()

  if (isLoading) {
    return <p>Loading dashboard...</p>
  }

  if (isError || !data) {
    return <p>Unable to load dashboard data.</p>
  }

  return (
    <section>
      <h1>Dashboard</h1>
      <div className="kpi-grid">
        <KpiCard title="Products Healthy" value={`${data.healthy_products}/${data.products_total}`} />
        <KpiCard title="Failing Checks" value={data.failing_checks} />
        <KpiCard title="SLA Compliance" value={`${data.sla_compliance_pct_24h}%`} />
        <KpiCard title="API p95 Latency" value={`${data.api_p95_latency_ms} ms`} />
      </div>

      <h2>Product Status</h2>
      <div className="product-grid">
        {data.products.map((product) => (
          <article key={product.id} className="product-card">
            <h3>{product.display_name}</h3>
            <StatusBadge status={product.health_status} />
            <p>Team: {product.owner_team}</p>
            <p>Freshness: {product.data_freshness_seconds}s</p>
          </article>
        ))}
      </div>
    </section>
  )
}
