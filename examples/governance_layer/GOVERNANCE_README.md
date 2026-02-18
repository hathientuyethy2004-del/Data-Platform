# Governance Layer - Complete Data Governance System

## Overview

The **Governance Layer** is an enterprise-grade data governance platform that provides comprehensive metadata management, data lineage tracking, quality monitoring, compliance management, access control, and data discovery capabilities.

## Architecture

The governance layer consists of 8 interconnected subsystems:

```
governance_layer/
├── config/                          # Configuration management
│   └── governance_config.py          # Central configuration for all subsystems
├── catalog/                          # Data asset metadata
│   └── data_catalog.py               # Asset registration, search, classification
├── lineage/                          # Data flow tracking
│   └── lineage_tracker.py            # Upstream/downstream analysis, impact assessment
├── quality/                          # Quality monitoring
│   └── quality_monitor.py            # SLA enforcement, anomaly detection, scorecards
├── access/                           # Access control & audit
│   └── access_control.py             # RBAC, API key management, audit logging
├── compliance/                       # Compliance & retention
│   └── compliance_tracker.py         # GDPR/CCPA/HIPAA/SOC2, data retention, RTBF
├── discovery/                        # Data discovery API
│   └── discovery_api.py              # FastAPI endpoints for asset search & exploration
├── dashboard/                        # Governance dashboard
│   └── governance_dashboard.py       # Real-time metrics & monitoring
└── test_governance_layer.py          # Integration tests & examples
```

## Core Components

### 1. Configuration Management (`governance_config.py`)

Central configuration system for all governance subsystems with 8 sub-configurations:

**Features:**
- Environment variable overrides for all settings
- Automatic directory creation
- Configuration validation
- Type-safe dataclasses

**Sub-configurations:**
- `CatalogConfig`: Metadata discovery, versioning, storage
- `LineageConfig`: Column-level tracking, impact analysis
- `QualityConfig`: SLA thresholds, anomaly detection
- `AccessControlConfig`: RBAC, API key expiry, audit retention
- `ComplianceConfig`: Frameworks (GDPR/CCPA/HIPAA/SOC2/FERPA), retention, encryption
- `DiscoveryConfig`: Full-text search, indexing, recommendations
- `DashboardConfig`: Port, refresh intervals, metrics tracking
- `DataStewardConfig`: Steward roles, escalation policies

**Usage:**
```python
from config.governance_config import governance_config

# Access configuration
print(governance_config.catalog.enable_catalog)
print(governance_config.compliance.compliance_frameworks)
```

### 2. Data Catalog (`data_catalog.py`)

Comprehensive asset metadata repository with 10+ capabilities.

**Key Features:**
- Asset registration with auto-generated UUIDs
- Multi-layer classification (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED, CLASSIFIED)
- PII tracking and sensitive data identification
- Tag-based organization and discovery
- Owner/team assignment
- Technical metadata (record count, size, schema)
- Quality scoring integration
- Version tracking
- Full-text search with fuzzy matching
- Asset relationships
- SLA tracking

**Asset Metadata:**
- Basic info: name, type, layer, platform, location
- Ownership: owner, email, team
- Classification and sensitivity
- Technical details: record count, size, columns, schema
- Compliance: frameworks, retention, GDPR/CCPA flags
- Quality: SLA thresholds, quality score
- Lineage: source/dependent assets
- Timestamps: created, updated, version

**Usage:**
```python
from catalog.data_catalog import get_catalog, DataAssetMetadata

catalog = get_catalog()

# Register asset
asset = DataAssetMetadata(
    asset_id="customer_bronze",
    name="Customer Data (Bronze)",
    asset_type="TABLE",
    layer="bronze",
    platform="parquet",
    location="/data/bronze/customers",
    owner="data_owner@company.com",
    owner_team="Data Engineering",
    description="Raw customer data from source systems",
    tags=["customers", "raw", "pii"],
    classification="RESTRICTED",
    contains_pii=True
)
asset_id = catalog.register_asset(asset)

# Search assets
results = catalog.search_assets("customer")

# Get by category
pii_assets = catalog.get_pii_assets()
layer_assets = catalog.get_assets_by_layer("bronze")

# Get report
report = catalog.get_catalog_report()
```

### 3. Data Lineage Tracker (`lineage_tracker.py`)

End-to-end data flow tracking with upstream/downstream analysis and impact assessment.

**Key Features:**
- Asset-to-asset transformation tracking
- Column-level lineage (which columns derived from which)
- Recursive upstream traversal (all data sources)
- Recursive downstream traversal (all consumers)
- Impact analysis with severity estimation
- Lineage graph visualization (nodes + edges format)
- Query optimization estimates
- Cycle detection
- Comprehensive reporting

**Impact Analysis:**
- Immediate impact: directly dependent assets
- Cascading impact: transitive dependencies
- Impact severity: low/medium/high
- Estimated update time for changes

**Usage:**
```python
from lineage.lineage_tracker import get_lineage_tracker

lineage = get_lineage_tracker()

# Record transformation
edge_id = lineage.record_lineage(
    source_asset="customer_bronze",
    target_asset="customer_silver",
    transformation_job="customer_etl_job",
    operation_type="transformation",
    created_by="etl_user@company.com"
)

# Get upstream lineage (all sources)
upstream = lineage.get_upstream_lineage("customer_silver", depth=3)

# Get downstream impact (all consumers)
downstream = lineage.get_downstream_lineage("customer_bronze")

# Analyze impact of changes
impact = lineage.get_impact_analysis("customer_bronze")
# Returns: {impact_level, directly_affected_count, all_affected, estimated_update_time}

# Get visualization data
graph = lineage.get_lineage_graph("customer_silver", depth=5)
# Returns: {root_asset, nodes, edges, totals}

# Get report
report = lineage.get_lineage_report()
```

### 4. Quality Monitor (`quality_monitor.py`)

Data quality management with SLA enforcement and anomaly detection.

**Key Features:**
- Quality check registration (freshness, completeness, accuracy, uniqueness, validity)
- Check execution and result tracking
- SLA threshold enforcement
- Automated anomaly detection (Z-score based)
- Weighted quality scorecards
- Quality report generation
- Historical trend analysis

**Quality Metrics:**
- **Freshness**: Data is up-to-date (hours since last update)
- **Completeness**: No missing values (% non-null)
- **Accuracy**: Valid records (% of correct data)
- **Uniqueness**: No duplicates (% unique)
- **Validity**: Format/type correct

**Scoring:**
- Per-metric scores: 0-100
- Weighted overall score (25% freshness, 25% completeness, 25% accuracy, 15% uniqueness, 10% validity)
- Status: excellent (95+), good (85+), fair (70+), poor (<70)

**Usage:**
```python
from quality.quality_monitor import get_quality_monitor

quality = get_quality_monitor()

# Register checks
check_id = quality.register_quality_check(
    asset_id="customer_bronze",
    check_type="completeness",
    metric_name="null_percentage",
    threshold=95  # Minimum 95% completeness
)

# Execute check
quality.execute_quality_check(check_id, 98)

# Or use convenience methods
is_fresh = quality.check_freshness(
    asset_id="customer_bronze",
    last_updated="2024-01-01T10:00:00",
    expected_hours=24
)

completeness = quality.check_completeness(
    asset_id="customer_bronze",
    total_records=1000,
    null_records=20
)

# Detect anomalies
anomaly = quality.detect_anomalies(
    asset_id="customer_bronze",
    metric_name="record_count",
    current_value=1000
)
# Returns: {current_value, expected_range, zscore, is_anomaly, severity}

# Calculate quality score
scorecard = quality.calculate_quality_score("customer_bronze")
# Returns: {freshness, completeness, accuracy, overall_score, status, checks_passed/failed}

# Enforce SLA
violations = quality.enforce_sla("customer_bronze")

# Get report
report = quality.get_quality_report(days=30)
```

### 5. Access Control (`access_control.py`)

Role-based access control (RBAC) with API key management and comprehensive audit logging.

**Key Features:**
- Role-based access control (7 predefined roles)
- API key generation and validation
- API key expiry management
- Rate limiting support
- IP whitelisting
- Comprehensive audit logging (90-day retention)
- Access report generation
- Audit trail export

**Predefined Roles:**
- `admin`: Full system access
- `data_owner`: Own data assets
- `data_steward`: Manage catalog/quality
- `analyst`: Query and analyze
- `developer`: API/SDK access
- `viewer`: Read-only access
- `auditor`: Audit logs only

**Permissions:**
- Per-role resource type access (asset, catalog, lineage, quality, policy, api, audit)
- Per-action access (read, write, delete, admin)
- Asset-level permissions
- Custom conditions support

**Usage:**
```python
from access.access_control import get_access_manager

access = get_access_manager()

# Grant role
access.grant_role("alice@company.com", "data_owner")

# Create API key
api_key = access.create_api_key(
    owner="alice@company.com",
    name="ML_Pipeline_Key",
    scopes=["read", "write"],
    expiry_days=90
)

# Validate API key
is_valid = access.validate_api_key(key_id, key)

# Revoke key
access.revoke_api_key(key_id)

# Check permission
has_permission = access.check_permission(
    user="alice@company.com",
    action="write",
    resource_type="catalog"
)

# Log audit event
log_id = access.log_audit_event(
    user="alice@company.com",
    action="register_asset",
    resource_type="catalog",
    resource_id="customer_bronze",
    status="success"
)

# Get audit logs
logs = access.get_audit_logs(user="alice@company.com", days=30)

# Get report
report = access.get_access_report()
```

### 6. Compliance Tracker (`compliance_tracker.py`)

Compliance management with support for multiple frameworks and right-to-be-forgotten (RTBF) processing.

**Supported Frameworks:**
- **GDPR**: EU data protection (encryption, retention, PII handling)
- **CCPA**: California privacy (privacy notices, opt-out, data subject rights)
- **HIPAA**: Healthcare (PHI encryption, access logging)
- **SOC2**: Service organization control (availability, confidentiality, integrity)
- **FERPA**: Educational data protection
- **Custom**: Custom compliance rules

**Key Features:**
- Retention policy management
- Right-to-be-forgotten (RTBF) request processing
- Framework-specific compliance assessment
- Deletion audit trail
- Encryption validation
- Policy enforcement
- Compliance reporting

**Compliance Assessment Checks:**
- PII encryption validation
- Retention policy enforcement
- Data ownership tracking
- Privacy notices
- Opt-out mechanisms
- Access logging
- Backup coverage
- Integrity checks

**Usage:**
```python
from compliance.compliance_tracker import get_compliance_tracker

compliance = get_compliance_tracker()

# Create retention policy
policy_id = compliance.create_retention_policy(
    asset_id="customer_bronze",
    framework="gdpr",
    retention_days=365,
    purge_after_days=730,
    description="GDPR compliant 1-year retention"
)

# Apply retention
result = compliance.apply_retention_policy("customer_bronze")

# Submit RTBF request
rtbf_id = compliance.submit_rtbf_request(
    data_subject_id="subject_12345",
    asset_ids=["customer_bronze", "customer_silver"],
    requested_by="privacy_officer@company.com",
    reason="Data subject exercised right to be forgotten"
)

# Process RTBF
rtbf_result = compliance.process_rtbf_request(rtbf_id)

# Assess compliance
assets = [...]  # List of asset dicts
report = compliance.assess_compliance("gdpr", assets)

# Get compliance summary
summary = compliance.generate_compliance_summary(frameworks=["gdpr", "ccpa"])

# Get deletion audit trail
audits = compliance.get_deletion_audit_trail(asset_id="customer_bronze", days=90)

# Export compliance data
compliance.export_compliance_data("/tmp/compliance_export.json")
```

### 7. Data Discovery API (`discovery_api.py`)

FastAPI-based REST API for asset search, exploration, and metadata retrieval.

**Endpoints:**
- `GET /health` - Health check
- `GET /search?query=...` - Full-text search
- `GET /assets?layer=...&owner=...&classification=...&tag=...` - Browse assets
- `GET /assets/{asset_id}` - Get asset details
- `GET /assets/{asset_id}/lineage?direction=...&depth=...` - Get lineage
- `GET /assets/{asset_id}/similar` - Get similar assets
- `GET /catalog/report` - Catalog statistics
- `GET /quality/report?days=...` - Quality metrics

**Features:**
- Authentication via API keys
- Pagination support
- Full-text search
- Multi-filter browsing
- Lineage visualization data
- Asset similarity recommendations
- Rate limiting
- Comprehensive REST responses

**Usage:**
```python
from discovery.discovery_api import get_discovery_api

discovery = get_discovery_api(port=8889)

# Start API server
# discovery.start()

# Access endpoints programmatically
# GET /search?query=customer
# GET /assets?owner=alice@company.com
# GET /assets/customer_bronze
# GET /assets/customer_bronze/lineage?direction=upstream&depth=3

# Export API specification
discovery.export_api_spec("/tmp/api_spec.json")
```

### 8. Governance Dashboard (`governance_dashboard.py`)

Real-time monitoring dashboard with multiple metric endpoints and HTML visualization.

**Dashboard Metrics:**
- Catalog health (total assets, PII count, unowned assets)
- Data quality (quality score %, excellent/good/fair/poor breakdown)
- Access control (active API keys, defined roles)
- Compliance status (frameworks, compliance percentage)
- Data lineage (transformations, sources, sinks)
- Storage utilization (by layer, total)
- Activity metrics (events by type, top users)

**Display Elements:**
- Overall health indicator
- Metric cards with KPIs
- Progress bars
- Status indicators
- Critical alerts
- Real-time updates

**Usage:**
```python
from dashboard.governance_dashboard import get_governance_dashboard

dashboard = get_governance_dashboard(port=8890)

# Start dashboard
# dashboard.start()

# Access endpoints
# GET / - Dashboard HTML
# GET /api/metrics - All metrics
# GET /api/catalog-metrics - Catalog only
# GET /api/quality-metrics - Quality only
# GET /api/access-metrics - Access control
# GET /api/compliance-metrics - Compliance
# GET /api/storage-metrics - Storage
# GET /api/activity-metrics - Activity logs

# Get metrics programmatically
metrics = dashboard.get_dashboard_metrics()
```

## Data Classifications

Assets can be classified at 5 levels:

1. **PUBLIC**: No restrictions, freely accessible
2. **INTERNAL**: Internal use only
3. **CONFIDENTIAL**: Business sensitive, restricted access
4. **RESTRICTED**: PII, financial data, highly sensitive - encrypted, audit logged
5. **CLASSIFIED**: Government classified, maximum security

## Installation & Setup

### Requirements
- Python 3.8+
- No external dependencies for core functionality
- Optional: FastAPI + Uvicorn (for API and dashboard)

### Installation

```bash
# Core governance layer (no dependencies)
cd governance_layer

# Optional: Install for API/Dashboard
pip install fastapi uvicorn

# Optional: Install for development
pip install pytest pytest-cov
```

### Configuration

Environment variables for overrides:

```bash
# Catalog
export GOVERNANCE_CATALOG_ENABLED=true
export GOVERNANCE_CATALOG_PATH=/data/governance/catalog

# Lineage
export GOVERNANCE_LINEAGE_ENABLED=true
export GOVERNANCE_LINEAGE_PATH=/data/governance/lineage

# Quality
export GOVERNANCE_QUALITY_ENABLED=true
export GOVERNANCE_QUALITY_SLA_FRESHNESS=24
export GOVERNANCE_QUALITY_SLA_COMPLETENESS=95

# Access
export GOVERNANCE_ACCESS_ENABLED=true
export GOVERNANCE_ACCESS_RBAC=true
export GOVERNANCE_ACCESS_AUDIT_RETENTION=730

# Compliance
export GOVERNANCE_COMPLIANCE_ENABLED=true
export GOVERNANCE_COMPLIANCE_FRAMEWORKS=gdpr,ccpa,hipaa

# Discovery
export GOVERNANCE_DISCOVERY_ENABLED=true
export GOVERNANCE_DISCOVERY_PORT=8889

# Dashboard
export GOVERNANCE_DASHBOARD_ENABLED=true
export GOVERNANCE_DASHBOARD_PORT=8890
```

## Usage Examples

### Example 1: Register a Data Asset

```python
from catalog.data_catalog import get_catalog, DataAssetMetadata

catalog = get_catalog()

asset = DataAssetMetadata(
    asset_id="transactions_bronze",
    name="Transaction Data (Bronze)",
    asset_type="TABLE",
    layer="bronze",
    platform="parquet",
    location="/data/bronze/transactions",
    owner="data_owner@company.com",
    owner_team="Data Engineering",
    classification="RESTRICTED",
    contains_pii=True,
    tags=["transactions", "pii"]
)

asset_id = catalog.register_asset(asset)
print(f"Asset registered: {asset_id}")
```

### Example 2: Track Data Lineage

```python
from lineage.lineage_tracker import get_lineage_tracker

lineage = get_lineage_tracker()

# Record ETL transformation
lineage.record_lineage(
    source_asset="transactions_bronze",
    target_asset="transactions_silver",
    transformation_job="txn_cleaning_job",
    operation_type="transformation"
)

# Get impact of changes
impact = lineage.get_impact_analysis("transactions_bronze")
print(f"Impact Level: {impact['impact_level']}")
print(f"Affected Assets: {impact['directly_affected_assets']}")
```

### Example 3: Monitor Data Quality

```python
from quality.quality_monitor import get_quality_monitor

quality = get_quality_monitor()

# Register and execute check
check_id = quality.register_quality_check(
    asset_id="transactions_bronze",
    check_type="completeness",
    metric_name="null_percent",
    threshold=95
)

quality.execute_quality_check(check_id, 97.5)

# Get quality score
scorecard = quality.calculate_quality_score("transactions_bronze")
print(f"Quality: {scorecard.overall_score:.1f}/100 ({scorecard.status})")

# Check for anomalies
anomaly = quality.detect_anomalies(
    asset_id="transactions_bronze",
    metric_name="record_count",
    current_value=5000000
)

if anomaly.is_anomaly:
    print(f"⚠️ Anomaly detected! Z-score: {anomaly.zscore}")
```

### Example 4: Manage GDPR Compliance

```python
from compliance.compliance_tracker import get_compliance_tracker

compliance = get_compliance_tracker()

# Submit right-to-be-forgotten request
rtbf_id = compliance.submit_rtbf_request(
    data_subject_id="user_98765",
    asset_ids=["transactions_bronze", "transactions_silver", "customer_gold"],
    requested_by="privacy_officer@company.com",
    reason="Article 17 - Right to be forgotten"
)

# Process deletion
result = compliance.process_rtbf_request(rtbf_id)
print(f"Processed {result['assets_processed']} assets")

# Get deletion audit trail
audits = compliance.get_deletion_audit_trail(
    asset_id="transactions_bronze",
    days=90
)

# Assess GDPR compliance
report = compliance.assess_compliance("gdpr", assets_list)
print(f"GDPR Status: {report.overall_status}")
```

### Example 5: API-Based Asset Search

```python
# Start API server (in separate process)
# from discovery.discovery_api import get_discovery_api
# api = get_discovery_api()
# api.start()

# Then make HTTP requests:
# GET /search?query=customer
# GET /assets?owner=alice@company.com&classification=RESTRICTED
# GET /assets/transactions_bronze/lineage?direction=upstream&depth=5
# GET /quality/report?days=30
```

### Example 6: Run Integration Tests

```bash
cd governance_layer
python test_governance_layer.py
```

## Data Storage

All governance data is stored as JSON files in the configured directories:

```
/governance/data/
├── catalog/
│   ├── assets.json              # Asset metadata
│   ├── columns.json             # Column definitions
│   ├── tags_index.json          # Tag lookup index
│   └── owners_index.json        # Owner lookup index
├── lineage/
│   ├── lineage_edges.json       # Asset transformations
│   └── column_lineage.json      # Column-level lineage
├── quality/
│   ├── quality_checks.json      # Check definitions
│   ├── quality_scores.json      # Quality scorecards
│   ├── anomalies.json           # Detected anomalies
│   └── sla_violations.json      # SLA breaches
├── access/
│   ├── roles.json               # Role definitions
│   ├── api_keys.json            # API keys
│   ├── audit_log.json           # Audit trail
│   └── user_*.json              # Per-user data
└── compliance/
    ├── retention_policies.json      # Retention rules
    ├── rtbf_requests.json           # RTBF requests
    ├── compliance_reports.json      # Assessment reports
    └── deletion_audit.json          # Deletion records
```

## Integration with Data Platform

### With Lakehouse Layer

```python
from governance.catalog.data_catalog import get_catalog
from governance.lineage.lineage_tracker import get_lineage_tracker
from governance.quality.quality_monitor import get_quality_monitor

# After ingesting data into Bronze Layer
catalog = get_catalog()
catalog.register_asset(bronze_asset)

# Track transformation to Silver
lineage = get_lineage_tracker()
lineage.record_lineage("bronze_table", "silver_table", "etl_job")

# Monitor quality
quality = get_quality_monitor()
quality.check_freshness("silver_table", last_update, 24)
quality.check_completeness("silver_table", total, nulls)
```

### With Processing Layer

```python
# Track Spark job transformations
lineage = get_lineage_tracker()
for source in spark_job_sources:
    for target in spark_job_targets:
        lineage.record_lineage(
            source_asset=source,
            target_asset=target,
            transformation_job=job_name,
            operation_type="spark_transform"
        )
```

### Compliance Automation

```python
# Scheduled job to enforce retention
compliance = get_compliance_tracker()
assets = catalog.get_assets_by_layer("bronze")
for asset in assets:
    compliance.apply_retention_policy(asset.asset_id)
```

## Security Considerations

1. **Data Encryption**: PII and RESTRICTED assets encrypted with AES-256
2. **Access Control**: RBAC with audit logging for all operations
3. **Audit Trail**: 90+ days of detailed audit logs with timestamps
4. **API Security**: API keys with expiry and per-action validation
5. **GDPR Compliance**: Right-to-be-forgotten support with deletion auditing
6. **Data Classification**: 5-level classification with enforcement
7. **Retention Policies**: Automatic data purging based on regulations

## Performance Considerations

- **Indexing**: Tag and owner indexes for O(1) lookup
- **Caching**: In-memory singleton instances reduce I/O
- **Batch Operations**: Support for bulk asset registration
- **Async APIs**: FastAPI async endpoints for non-blocking I/O
- **Pagination**: Large result sets paginated
- **Compression**: JSON storage with optional compression

## Best Practices

1. **Register early**: Register data assets immediately upon creation
2. **Tag consistently**: Use consistent tagging scheme across organization
3. **Own assets**: Always assign clear owner/team for every asset
4. **Monitor quality**: Set appropriate SLA thresholds for each layer
5. **Track lineage**: Record all significant transformations
6. **Review compliance**: Regular compliance assessments (quarterly minimum)
7. **Audit access**: Monitor API key usage and audit logs
8. **Document assets**: Provide clear descriptions for discovery

## Troubleshooting

### Issue: Assets not appearing in search
- Check tags and filters
- Verify catalog is enabled
- Ensure asset was registered (check assets.json)

### Issue: Lineage not tracking
- Verify record_lineage calls are made
- Check lineage_edges.json for entries
- Ensure source/target asset IDs are correct

### Issue: Quality checks fail
- Verify check was registered
- Check actual value against threshold
- Review quality_checks.json for definition

### Issue: RTBF request not processing
- Verify request status
- Check deletion audit trail
- Ensure compliance tracker initialized

## License & Support

This governance layer is part of the Data Platform.

For questions or issues, please refer to the main platform documentation.

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready
