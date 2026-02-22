import type { HealthStatus } from '../../api/contracts'

type StatusBadgeProps = {
  status: HealthStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const className = `status-badge status-${status}`
  return <span className={className}>{status}</span>
}
