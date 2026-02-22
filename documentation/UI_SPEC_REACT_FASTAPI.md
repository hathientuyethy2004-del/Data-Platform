# Data Platform UI Spec (React + FastAPI)

## 1) Scope & Goals

This spec defines a production-ready UI/UX contract for the Data Platform console based on:
- Frontend: React + TypeScript
- Backend: FastAPI (REST-first)
- Data domains: web-user-analytics, mobile-user-analytics, user-segmentation, operational-metrics, compliance-auditing

### Product Goals
- One unified control plane for platform health and product operations.
- Fast drill-down from global status to product-level diagnostics.
- Shared language between frontend and backend via explicit API contracts.

### Non-goals (MVP)
- No custom query builder UI.
- No workflow designer.
- No role management UI editor.

---

## 2) High-Level Architecture

### 2.1 Frontend (React)
- Framework: React 18 + TypeScript
- Routing: React Router
- Server state: TanStack Query
- UI primitives: design-system components (cards, tables, badges, tabs, drawers, charts)
- Form handling: React Hook Form + Zod
- Auth token handling: HTTP-only cookie or Bearer token (environment dependent)

### 2.2 Backend (FastAPI)
- API style: REST JSON
- Validation: Pydantic v2
- Error contract: normalized `error.code`, `error.message`, `request_id`
- Health/readiness endpoints for gateway + product services

### 2.3 Integration Pattern
- UI never calls product services directly in MVP.
- UI calls the Platform API Gateway only.
- Gateway proxies or aggregates product endpoints.

---

## 3) Information Architecture (Screens)

### 3.1 App Shell
- Left navigation:
  - Dashboard
  - Products
  - Data Lake
  - Governance
  - Platform Ops
  - Settings
- Top bar:
  - Environment selector (dev/staging/prod)
  - Global search
  - Notifications
  - User menu

### 3.2 Dashboard Screen
Purpose: global situational awareness.

#### Sections
1. System KPI strip
   - Products Healthy
   - Failing Checks
   - SLA Compliance %
   - API p95 Latency
2. Product Status Grid (5 cards)
3. Active Alerts Timeline
4. Recent Executions (tests, demos, jobs)

#### Required Data
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/alerts?status=open&limit=20`
- `GET /api/v1/executions?limit=20`

### 3.3 Products List Screen
Purpose: manage all products in one place.

#### Sections
- Filter bar: status, environment, owner team
- Products table:
  - name
  - health
  - last test result
  - last deploy time
  - data freshness
  - quick actions

#### Actions
- View detail
- Run test
- Run demo
- Open logs

#### Required Data
- `GET /api/v1/products`
- `POST /api/v1/products/{product_id}/tests/run`
- `POST /api/v1/products/{product_id}/demos/run`

### 3.4 Product Detail Screen
Purpose: operate and diagnose a single product.

#### Header
- Product name, status badge, owner, SLA target, environment switch

#### Tabs
1. Overview
   - Health summary cards
   - Last 24h events
2. Pipelines
   - Ingestion/processing/storage jobs list
   - Job state + duration + retries
3. APIs
   - Endpoint health, error rate, latency chart
4. Tests
   - Latest test runs + pass rate trend
5. Monitoring
   - SLA compliance chart
   - freshness lag
6. Config
   - Read-only effective config + source (default/env override)

#### Required Data
- `GET /api/v1/products/{product_id}`
- `GET /api/v1/products/{product_id}/health`
- `GET /api/v1/products/{product_id}/pipelines/runs`
- `GET /api/v1/products/{product_id}/apis/metrics`
- `GET /api/v1/products/{product_id}/tests/runs`
- `GET /api/v1/products/{product_id}/monitoring/sla`
- `GET /api/v1/products/{product_id}/config/effective`

### 3.5 Data Lake Screen
Purpose: monitor Bronze/Silver/Gold datasets.

#### Sections
- Dataset explorer tree (product -> layer -> table)
- Table metadata panel:
  - row count
  - partitions
  - last update
  - schema version
- Freshness and quality indicators

#### Required Data
- `GET /api/v1/datalake/datasets`
- `GET /api/v1/datalake/datasets/{dataset_id}`
- `GET /api/v1/datalake/datasets/{dataset_id}/quality`

### 3.6 Governance Screen
Purpose: auditability and policy visibility.

#### Sections
- Access log stream
- Data lineage graph (simplified)
- Retention and compliance policy table
- Violation incidents list

#### Required Data
- `GET /api/v1/governance/access-logs`
- `GET /api/v1/governance/lineage?entity_id=...`
- `GET /api/v1/governance/policies`
- `GET /api/v1/governance/incidents`

### 3.7 Platform Ops Screen
Purpose: platform-level operations.

#### Sections
- Orchestrator status
- API gateway status + upstream service status
- Service registry by environment
- Execution queue / recent platform tasks

#### Required Data
- `GET /api/v1/platform/status`
- `GET /api/v1/platform/services`
- `GET /api/v1/platform/executions`
- `POST /api/v1/platform/actions/{action}`

### 3.8 Settings Screen
Purpose: user-level preferences (MVP minimal).

#### Sections
- Notification preferences
- Default environment
- Timezone / locale

#### Required Data
- `GET /api/v1/me/preferences`
- `PATCH /api/v1/me/preferences`

---

## 4) Component Specification

### 4.1 Core Components
1. `AppShell`
   - props: `navItems`, `currentEnv`, `onEnvChange`, `children`
2. `StatusBadge`
   - states: `healthy | warning | critical | skipped | unknown`
3. `KpiCard`
   - props: `title`, `value`, `delta`, `trend`, `loading`
4. `ProductCard`
   - props: `product`, `onOpen`, `onRunTest`, `onRunDemo`
5. `DataTable<T>`
   - server pagination, sorting, filters, empty/loading/error states
6. `ExecutionTimeline`
   - mixed event feed with status markers
7. `HealthChart`
   - SLA %, error rate, latency trends
8. `JsonViewer`
   - render effective config + copy/download
9. `ConfirmActionDialog`
   - required for run test/demo/action commands

### 4.2 UX States (All screens)
- Loading: skeletons (not spinner-only)
- Empty: clear CTA + explanation
- Error: retry + request id
- Partial failure: degraded banner with fallback data

### 4.3 Accessibility
- Keyboard-first navigation in tables/dialogs
- WCAG AA contrast
- ARIA labels for status and charts

---

## 5) API Contract (FastAPI)

### 5.1 Conventions
- Base path: `/api/v1`
- Auth: `Authorization: Bearer <token>` (or session cookie)
- Traceability: `X-Request-ID` accepted and echoed
- Time format: ISO 8601 UTC

#### Standard Success Envelope
```json
{
  "data": {},
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-02-21T17:10:00Z"
  }
}
```

#### Standard Error Envelope
```json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product not found",
    "details": {}
  },
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-02-21T17:10:00Z"
  }
}
```

### 5.2 Domain Models (API)

#### ProductSummary
```json
{
  "id": "web-user-analytics",
  "display_name": "Web User Analytics",
  "owner_team": "analytics-web",
  "environment": "dev",
  "health_status": "healthy",
  "last_test": {
    "status": "success",
    "passed": 21,
    "failed": 0,
    "completed_at": "2026-02-21T17:02:15Z"
  },
  "data_freshness_seconds": 120,
  "sla_compliance_pct_24h": 99.95
}
```

#### ExecutionRecord
```json
{
  "execution_id": "exe_20260221_001",
  "scope": "product",
  "target": "web-user-analytics",
  "type": "test_run",
  "status": "success",
  "started_at": "2026-02-21T17:02:10Z",
  "finished_at": "2026-02-21T17:02:15Z",
  "duration_seconds": 5.1,
  "triggered_by": "user:alice"
}
```

#### Alert
```json
{
  "id": "al_1001",
  "severity": "warning",
  "source": "operational-metrics",
  "title": "Data freshness lag > threshold",
  "status": "open",
  "created_at": "2026-02-21T16:50:00Z",
  "last_seen_at": "2026-02-21T17:00:00Z"
}
```

### 5.3 Endpoint Matrix

#### Dashboard
- `GET /api/v1/dashboard/summary`
  - response: global KPI + product status summary

#### Products
- `GET /api/v1/products`
  - query: `environment`, `status`, `owner_team`, `page`, `page_size`
- `GET /api/v1/products/{product_id}`
- `GET /api/v1/products/{product_id}/health`
- `POST /api/v1/products/{product_id}/tests/run`
- `POST /api/v1/products/{product_id}/demos/run`
- `GET /api/v1/products/{product_id}/tests/runs`
- `GET /api/v1/products/{product_id}/pipelines/runs`
- `GET /api/v1/products/{product_id}/apis/metrics`
- `GET /api/v1/products/{product_id}/monitoring/sla`
- `GET /api/v1/products/{product_id}/config/effective`

#### Data Lake
- `GET /api/v1/datalake/datasets`
- `GET /api/v1/datalake/datasets/{dataset_id}`
- `GET /api/v1/datalake/datasets/{dataset_id}/quality`

#### Governance
- `GET /api/v1/governance/access-logs`
- `GET /api/v1/governance/lineage`
- `GET /api/v1/governance/policies`
- `GET /api/v1/governance/incidents`

#### Platform
- `GET /api/v1/platform/status`
- `GET /api/v1/platform/services`
- `GET /api/v1/platform/executions`
- `POST /api/v1/platform/actions/{action}`

#### User Preferences
- `GET /api/v1/me/preferences`
- `PATCH /api/v1/me/preferences`

---

## 6) FastAPI Router Layout (Proposed)

```text
shared/platform/api/
  __init__.py
  main.py
  deps.py
  schemas/
    common.py
    dashboard.py
    products.py
    datalake.py
    governance.py
    platform.py
    me.py
  routers/
    dashboard.py
    products.py
    datalake.py
    governance.py
    platform.py
    me.py
  services/
    orchestrator_service.py
    gateway_service.py
    monitoring_service.py
```

---

## 7) Frontend Project Layout (Proposed)

```text
frontend/
  src/
    app/
      providers/
      routes/
      layout/
    pages/
      DashboardPage/
      ProductsPage/
      ProductDetailPage/
      DataLakePage/
      GovernancePage/
      PlatformOpsPage/
      SettingsPage/
    components/
      common/
      product/
      charts/
      tables/
    features/
      dashboard/
      products/
      datalake/
      governance/
      platform/
      me/
    api/
      client.ts
      contracts.ts
      endpoints.ts
    styles/
```

---

## 8) Frontend Type Contracts (TypeScript)

```ts
export type HealthStatus = "healthy" | "warning" | "critical" | "skipped" | "unknown";

export interface ProductSummary {
  id: string;
  display_name: string;
  owner_team: string;
  environment: "dev" | "staging" | "prod";
  health_status: HealthStatus;
  data_freshness_seconds: number;
  sla_compliance_pct_24h: number;
  last_test?: {
    status: "success" | "failed" | "running" | "skipped";
    passed: number;
    failed: number;
    completed_at: string;
  };
}

export interface ApiEnvelope<T> {
  data: T;
  meta: {
    request_id: string;
    timestamp: string;
  };
}
```

---

## 9) Security & Permissions (MVP)

Roles:
- `viewer`: read-only access to all monitoring views.
- `operator`: viewer + run test/demo actions.
- `admin`: operator + platform actions + settings write.

Frontend behavior:
- Hide/disable action buttons if role is insufficient.
- Always enforce authorization server-side (UI is not security boundary).

---

## 10) Performance & Reliability Targets

- Dashboard initial load: < 2s (p95)
- Product detail tab switch: < 1s (cached)
- API p95 latency for read endpoints: < 500ms
- Action endpoints (`/tests/run`, `/demos/run`) should return within < 2s with async execution id.

---

## 11) Implementation Plan (3 Iterations)

### Iteration 1 (1-2 weeks): MVP Operations Console
- Build app shell + dashboard + products list/detail (overview/tests tabs)
- Implement products + dashboard + platform status APIs
- Add run test/demo actions with execution records

### Iteration 2 (1-2 weeks): Data & Governance Views
- Add Data Lake and Governance pages
- Implement lineage, policies, incidents, dataset quality APIs

### Iteration 3 (1 week): Hardening
- Role-based UI controls
- Error observability (request id propagation)
- Empty/error/skeleton states complete
- E2E tests for critical flows
- Pre-merge gate standardized with `./pre_merge_tests.sh` (shared tests + ordered product suites)

---

## 12) Acceptance Criteria

1. User can see all 5 products with live health status.
2. User can run test/demo for a product and observe execution status updates.
3. Dashboard shows system-level KPIs and open alerts.
4. Data Lake and Governance views load with valid backend contracts.
5. All API responses follow standardized envelope and error model.
6. UI passes core accessibility checks (keyboard + contrast + labels).
7. PR is merged only when `./pre_merge_tests.sh` passes.

---

## 13) Open Questions (To Confirm)

1. Authentication mode for internal users: SSO/OIDC vs static token.
2. Real-time updates approach: polling (MVP) vs WebSocket/SSE.
3. Source of truth for lineage graph: existing catalog vs new service.
4. Need for multi-tenant isolation in v1 or post-v1.
