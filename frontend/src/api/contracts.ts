export type HealthStatus = 'healthy' | 'warning' | 'critical' | 'skipped' | 'unknown'

export interface ApiMeta {
  request_id: string
  timestamp: string
}

export interface ApiEnvelope<T> {
  data: T
  meta: ApiMeta
}

export interface ProductLastTest {
  status: 'success' | 'failed' | 'running' | 'skipped'
  passed: number
  failed: number
  completed_at: string
}

export interface ProductSummary {
  id: string
  display_name: string
  owner_team: string
  environment: 'dev' | 'staging' | 'prod'
  health_status: HealthStatus
  data_freshness_seconds: number
  sla_compliance_pct_24h: number
  last_test?: ProductLastTest
}

export interface DashboardSummary {
  products_total: number
  healthy_products: number
  failing_checks: number
  sla_compliance_pct_24h: number
  api_p95_latency_ms: number
  products: ProductSummary[]
}

export interface ProductDetail {
  id: string
  display_name: string
  owner_team: string
  environment: 'dev' | 'staging' | 'prod'
  health_status: HealthStatus
  description: string
  sla_target_pct: number
}

export interface DataLakeDatasetSummary {
  id: string
  product_id: string
  layer: 'bronze' | 'silver' | 'gold'
  table_name: string
  freshness_seconds: number
}

export interface DataLakeDatasetDetail {
  id: string
  product_id: string
  layer: 'bronze' | 'silver' | 'gold'
  table_name: string
  schema_version: string
}

export interface DataLakeDatasetQuality {
  dataset_id: string
  quality_score: number
  checks_passed: number
  checks_failed: number
}

export interface GovernanceAccessLog {
  user: string
  resource: string
  action: string
  timestamp: string
}

export interface GovernanceLineage {
  nodes: string[]
  edges: [string, string][]
}

export interface GovernancePolicy {
  id: string
  name: string
  status: string
}

export interface GovernanceIncident {
  id: string
  severity: HealthStatus
  title: string
  status: string
  created_at: string
}

export interface PlatformStatus {
  products_total: number
  products_complete: number
  products_incomplete: number
  platform_components: Record<string, unknown>
}

export interface PlatformService {
  name: string
  base_url: string
  status: string
}

export interface PlatformExecution {
  execution_id: string
  scope: string
  target: string
  type: string
  status: string
  started_at: string
  finished_at: string
  duration_seconds: string
  triggered_by: string
}

export interface PlatformActionResult {
  action: string
  status: string
  triggered_by: string
}

export interface UserProfile {
  subject: string
  role: 'viewer' | 'operator' | 'admin'
}

export interface UserPreferences {
  default_environment: 'dev' | 'staging' | 'prod'
  timezone: string
  locale: string
  notifications_enabled: boolean
}

export interface PreferencesUpdate {
  default_environment?: 'dev' | 'staging' | 'prod'
  timezone?: string
  locale?: string
  notifications_enabled?: boolean
}
