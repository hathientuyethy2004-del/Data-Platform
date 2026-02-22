type KpiCardProps = {
  title: string
  value: string | number
  subtitle?: string
}

export function KpiCard({ title, value, subtitle }: KpiCardProps) {
  return (
    <article className="kpi-card">
      <p className="kpi-title">{title}</p>
      <p className="kpi-value">{value}</p>
      {subtitle ? <p className="kpi-subtitle">{subtitle}</p> : null}
    </article>
  )
}
