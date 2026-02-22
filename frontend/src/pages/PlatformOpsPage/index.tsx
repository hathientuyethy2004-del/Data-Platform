import { useAuth } from '../../app/providers/AuthProvider'
import { DataTable } from '../../components/common/DataTable'
import type {
  PlatformExecution,
  PlatformService,
} from '../../api/contracts'
import {
  usePlatformExecutions,
  usePlatformServices,
  usePlatformStatus,
  useRunPlatformAction,
} from '../../features/platform/usePlatformOps'

export function PlatformOpsPage() {
  const { role, isAdmin } = useAuth()
  const status = usePlatformStatus()
  const services = usePlatformServices()
  const executions = usePlatformExecutions()
  const runAction = useRunPlatformAction()

  if (status.isLoading || services.isLoading || executions.isLoading) {
    return <p>Loading platform operations...</p>
  }

  if (status.isError || services.isError || executions.isError || !status.data) {
    return <p>Unable to load platform operations data.</p>
  }

  return (
    <section>
      <h1>Platform Ops</h1>
      <div className="kpi-grid">
        <article className="kpi-card">
          <p className="kpi-title">Products Total</p>
          <p className="kpi-value">{status.data.products_total}</p>
        </article>
        <article className="kpi-card">
          <p className="kpi-title">Products Complete</p>
          <p className="kpi-value">{status.data.products_complete}</p>
        </article>
        <article className="kpi-card">
          <p className="kpi-title">Products Incomplete</p>
          <p className="kpi-value">{status.data.products_incomplete}</p>
        </article>
      </div>

      <h2 className="section-gap">Platform Components</h2>
      <DataTable<{ component: string; value: string }>
        rows={Object.entries(status.data.platform_components).map(([component, value]) => ({
          component,
          value: String(value),
        }))}
        emptyText="No component status available"
        columns={[
          { key: 'component', header: 'Component', render: (row) => row.component },
          { key: 'value', header: 'Status', render: (row) => row.value },
        ]}
      />

      <h2 className="section-gap">Service Registry</h2>
      <DataTable<PlatformService>
        rows={services.data ?? []}
        emptyText="No services found"
        columns={[
          { key: 'name', header: 'Service', render: (row) => row.name },
          { key: 'url', header: 'Base URL', render: (row) => row.base_url },
          { key: 'status', header: 'Status', render: (row) => row.status },
        ]}
      />

      <h2 className="section-gap">Recent Executions</h2>
      <DataTable<PlatformExecution>
        rows={executions.data ?? []}
        emptyText="No executions found"
        columns={[
          { key: 'id', header: 'Execution ID', render: (row) => row.execution_id },
          { key: 'target', header: 'Target', render: (row) => row.target },
          { key: 'type', header: 'Type', render: (row) => row.type },
          { key: 'status', header: 'Status', render: (row) => row.status },
          { key: 'duration', header: 'Duration (s)', render: (row) => row.duration_seconds },
          { key: 'by', header: 'Triggered By', render: (row) => row.triggered_by },
        ]}
      />

      <h2 className="section-gap">Actions</h2>
      <div className="actions-row">
        <button
          type="button"
          disabled={!isAdmin || runAction.isPending}
          title={isAdmin ? 'Run platform action' : `Role ${role ?? 'anonymous'} cannot run platform actions`}
          onClick={() => runAction.mutate('sync-services')}
        >
          {runAction.isPending ? 'Running...' : 'Sync services'}
        </button>
        <button
          type="button"
          disabled={!isAdmin || runAction.isPending}
          title={isAdmin ? 'Run platform action' : `Role ${role ?? 'anonymous'} cannot run platform actions`}
          onClick={() => runAction.mutate('health-check')}
        >
          {runAction.isPending ? 'Running...' : 'Run health check'}
        </button>
      </div>
      {runAction.isSuccess ? (
        <p className="section-gap">
          Action {runAction.data.action} status: {runAction.data.status}
        </p>
      ) : null}
      <p>Current role: {role ?? 'anonymous'}</p>
      {!isAdmin ? <p>Platform actions endpoint requires admin role.</p> : null}
    </section>
  )
}
