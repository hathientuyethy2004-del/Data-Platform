import { useMemo } from 'react'
import { DataTable } from '../../components/common/DataTable'
import { StatusBadge } from '../../components/common/StatusBadge'
import type { GovernanceAccessLog, GovernanceIncident, GovernancePolicy } from '../../api/contracts'
import {
  useAccessLogs,
  useIncidents,
  useLineage,
  usePolicies,
} from '../../features/governance/useGovernance'

export function GovernancePage() {
  const accessLogs = useAccessLogs()
  const lineage = useLineage()
  const policies = usePolicies()
  const incidents = useIncidents()

  const policyRows = useMemo(() => policies.data ?? [], [policies.data])
  const incidentRows = useMemo(() => incidents.data ?? [], [incidents.data])
  const accessRows = useMemo(() => accessLogs.data ?? [], [accessLogs.data])

  if (accessLogs.isLoading || lineage.isLoading || policies.isLoading || incidents.isLoading) {
    return <p>Loading governance data...</p>
  }

  if (accessLogs.isError || lineage.isError || policies.isError || incidents.isError) {
    return <p>Unable to load governance data.</p>
  }

  return (
    <section>
      <h1>Governance</h1>

      <article className="product-card section-gap">
        <h2>Lineage</h2>
        {lineage.data ? (
          <>
            <p>Nodes: {lineage.data.nodes.length}</p>
            <p>Edges: {lineage.data.edges.length}</p>
            <div className="lineage-list">
              {lineage.data.edges.map(([from, to]) => (
                <p key={`${from}-${to}`}>
                  {from} → {to}
                </p>
              ))}
            </div>
          </>
        ) : (
          <p>No lineage graph.</p>
        )}
      </article>

      <h2 className="section-gap">Policies</h2>
      <DataTable<GovernancePolicy>
        rows={policyRows}
        emptyText="No policies found"
        columns={[
          { key: 'id', header: 'Policy ID', render: (row) => row.id },
          { key: 'name', header: 'Name', render: (row) => row.name },
          { key: 'status', header: 'Status', render: (row) => row.status },
        ]}
      />

      <h2 className="section-gap">Incidents</h2>
      <DataTable<GovernanceIncident>
        rows={incidentRows}
        emptyText="No incidents"
        columns={[
          { key: 'id', header: 'Incident ID', render: (row) => row.id },
          { key: 'title', header: 'Title', render: (row) => row.title },
          { key: 'status', header: 'Status', render: (row) => row.status },
          { key: 'severity', header: 'Severity', render: (row) => <StatusBadge status={row.severity} /> },
          { key: 'createdAt', header: 'Created', render: (row) => row.created_at },
        ]}
      />

      <h2 className="section-gap">Access Logs</h2>
      <DataTable<GovernanceAccessLog>
        rows={accessRows}
        emptyText="No access logs"
        columns={[
          { key: 'user', header: 'User', render: (row) => row.user },
          { key: 'resource', header: 'Resource', render: (row) => row.resource },
          { key: 'action', header: 'Action', render: (row) => row.action },
          { key: 'time', header: 'Timestamp', render: (row) => row.timestamp },
        ]}
      />
    </section>
  )
}
