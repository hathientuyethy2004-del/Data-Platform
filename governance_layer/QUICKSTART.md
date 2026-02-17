# Quick Start Guide - Governance Layer

## 5-Minute Setup

### Step 1: Import Core Components

```python
from governance_layer.config.governance_config import governance_config
from governance_layer.catalog.data_catalog import get_catalog
from governance_layer.lineage.lineage_tracker import get_lineage_tracker
from governance_layer.quality.quality_monitor import get_quality_monitor
from governance_layer.access.access_control import get_access_manager
from governance_layer.compliance.compliance_tracker import get_compliance_tracker
```

### Step 2: Register Your First Asset

```python
from governance_layer.catalog.data_catalog import get_catalog, DataAssetMetadata

catalog = get_catalog()

# Create asset
asset = DataAssetMetadata(
    asset_id="my_first_asset",
    name="My Data Table",
    asset_type="TABLE",
    layer="bronze",
    platform="parquet",
    location="/data/my_table",
    owner="your_email@company.com",
    owner_team="Your Team",
    description="My first governed data asset",
    tags=["important", "daily"],
    classification="INTERNAL"
)

# Register
asset_id = catalog.register_asset(asset)
print(f"✓ Asset registered: {asset_id}")
```

**Output:**
```
✓ Asset registered: 550e8400-e29b-41d4-a716-446655440000
```

### Step 3: Monitor Quality

```python
from governance_layer.quality.quality_monitor import get_quality_monitor

quality = get_quality_monitor()

# Register quality check
check_id = quality.register_quality_check(
    asset_id="my_first_asset",
    check_type="completeness",
    metric_name="null_percentage",
    threshold=95  # Must be >= 95% complete
)

# Execute check
quality.execute_quality_check(check_id, 98.5)

# Get score
scorecard = quality.calculate_quality_score("my_first_asset")
print(f"Quality: {scorecard.overall_score:.1f}/100 ({scorecard.status})")
```

**Output:**
```
Quality: 98.5/100 (excellent)
```

### Step 4: Track Lineage

```python
from governance_layer.lineage.lineage_tracker import get_lineage_tracker

lineage = get_lineage_tracker()

# Record transformation
lineage.record_lineage(
    source_asset="my_first_asset",
    target_asset="my_processed_asset",
    transformation_job="my_etl_job",
    operation_type="transformation"
)

print("✓ Lineage recorded")

# Check impact
impact = lineage.get_impact_analysis("my_first_asset")
print(f"Impact: {impact['impact_level']}")
```

**Output:**
```
✓ Lineage recorded
Impact: medium
```

### Step 5: Control Access

```python
from governance_layer.access.access_control import get_access_manager

access = get_access_manager()

# Grant role
access.grant_role("colleague@company.com", "analyst")

# Create API key
api_key = access.create_api_key(
    owner="colleague@company.com",
    name="Analytics_Pipeline",
    expiry_days=90
)

print(f"✓ API Key created (keep secret): {api_key[:20]}...")

# Log access
access.log_audit_event(
    user="colleague@company.com",
    action="viewed_asset",
    resource_type="catalog",
    resource_id="my_first_asset",
    status="success"
)
```

**Output:**
```
✓ API Key created (keep secret): xxx:xxx...
```

### Step 6: View Dashboard

```python
from governance_layer.dashboard.governance_dashboard import get_governance_dashboard

dashboard = get_governance_dashboard()

# Get metrics
metrics = dashboard.get_dashboard_metrics()
print(f"Overall Status: {metrics['overall_status']}")
print(f"Assets: {metrics['catalog']['total_assets']}")
print(f"Quality: {metrics['quality']['quality_percentage']:.1f}%")
```

**Output:**
```
Overall Status: healthy
Assets: 1
Quality: 98.5%
```

## Common Tasks

### Search for Assets

```python
catalog = get_catalog()

# Full-text search
results = catalog.search_assets("customer")

# Filter by layer
bronze_assets = catalog.get_assets_by_layer("bronze")

# Filter by owner
my_assets = catalog.get_assets_by_owner("your_email@company.com")

# Filter by tags
pii_assets = catalog.get_assets_by_tag("pii")

for asset in results:
    print(f"- {asset.name} ({asset.asset_type}) [{asset.layer}]")
```

### Get Asset Details

```python
asset = catalog.get_asset("my_first_asset")

print(f"Name: {asset.name}")
print(f"Owner: {asset.owner}")
print(f"Classification: {asset.classification}")
print(f"Contains PII: {asset.contains_pii}")
print(f"Tags: {asset.tags}")
print(f"Description: {asset.description}")
```

### Track Data Origin

```python
lineage = get_lineage_tracker()

# "Where did this data come from?"
upstream = lineage.get_upstream_lineage("my_processed_asset", depth=5)
print(f"Source tables: {upstream['all_sources']}")

# "Who uses this data?"
downstream = lineage.get_downstream_lineage("my_first_asset")
print(f"Consumer tables: {downstream['all_consumers']}")

# "What will break if I change this?"
impact = lineage.get_impact_analysis("my_first_asset")
print(f"Affected assets: {impact['all_affected']}")
```

### Check Data Quality

```python
quality = get_quality_monitor()

# Check freshness (how old is data)
is_fresh = quality.check_freshness(
    asset_id="my_first_asset",
    last_updated="2024-01-15T10:30:00",
    expected_hours=24
)

# Check completeness (missing values)
completeness = quality.check_completeness(
    asset_id="my_first_asset",
    total_records=10000,
    null_records=150
)
print(f"Completeness: {completeness:.1f}%")

# Detect anomalies
anomaly = quality.detect_anomalies(
    asset_id="my_first_asset",
    metric_name="daily_record_count",
    current_value=10000
)

if anomaly.is_anomaly:
    print(f"⚠️ Anomaly: {anomaly.severity} (Z-score: {anomaly.zscore:.2f})")
```

### Manage GDPR Compliance

```python
compliance = get_compliance_tracker()

# Set up retention policy
policy_id = compliance.create_retention_policy(
    asset_id="my_first_asset",
    framework="gdpr",
    retention_days=365,
    purge_after_days=730
)
print(f"✓ Retention policy: Keep {365} days, purge after {730}")

# Handle right-to-be-forgotten request
rtbf_id = compliance.submit_rtbf_request(
    data_subject_id="user_12345",
    asset_ids=["my_first_asset"],
    requested_by="privacy@company.com",
    reason="User requested deletion"
)

result = compliance.process_rtbf_request(rtbf_id)
print(f"✓ Processed RTBF for {result['assets_processed']} assets")

# Check compliance status
summary = compliance.generate_compliance_summary(frameworks=["gdpr"])
print(f"GDPR Status: {summary['overall_status']}")
```

### Generate Reports

```python
# Catalog report
catalog_report = catalog.get_catalog_report()
print(f"Total assets: {catalog_report['total_assets']}")
print(f"PII assets: {catalog_report['pii_assets_count']}")

# Export catalog
catalog.export_catalog("/tmp/catalog_export.json")

# Quality report
quality_report = quality.get_quality_report(days=30)
print(f"Quality score: {quality_report['total_assets_monitored']} assets monitored")

# Export quality data
quality.export_quality_data("/tmp/quality_export.json")

# Lineage report
lineage_report = lineage.get_lineage_report()
print(f"Lineage: {lineage_report['edges_count']} transformations tracked")

# Export lineage
lineage.export_lineage("/tmp/lineage_export.json")

# Access report
access_report = access.get_access_report()
print(f"API Keys: {access_report['api_keys']['active']} active")

# Compliance report
compliance_export_path = compliance.export_compliance_data("/tmp/compliance_export.json")
```

## Using the REST API

### Start API Server

```python
from governance_layer.discovery.discovery_api import get_discovery_api

api = get_discovery_api(port=8889)
api.start()  # http://localhost:8889
```

### API Endpoints

```bash
# Health check
curl http://localhost:8889/health

# Search assets
curl "http://localhost:8889/search?query=customer&limit=10"

# Browse by filter
curl "http://localhost:8889/assets?owner=alice@company.com"

# Get asset details
curl http://localhost:8889/assets/my_first_asset

# Get lineage
curl "http://localhost:8889/assets/my_first_asset/lineage?direction=upstream&depth=3"

# Find similar assets
curl http://localhost:8889/assets/my_first_asset/similar

# Catalog metrics
curl http://localhost:8889/catalog/report

# Quality metrics
curl "http://localhost:8889/quality/report?days=30"
```

### With Authentication

```bash
# Using API key header
curl -H "api_key: {key_id}:{secret_key}" \
  http://localhost:8889/search?query=customer
```

## Using the Dashboard

### Start Dashboard

```python
from governance_layer.dashboard.governance_dashboard import get_governance_dashboard

dashboard = get_governance_dashboard(port=8890)
dashboard.start()  # http://localhost:8890
```

### Dashboard Metrics

**Visit http://localhost:8890**

Shows in real-time:
- 📊 Catalog health (assets, PII count)
- 📈 Data quality (quality score, SLA violations)
- 🔐 Access control (API keys, roles)
- ⚖️ Compliance (GDPR, CCPA, HIPAA status)
- 📊 Lineage (transformations, sources/sinks)
- 💾 Storage usage
- Overall governance health

Access JSON metrics at:
- `/api/metrics` - All metrics
- `/api/catalog-metrics` - Catalog only
- `/api/quality-metrics` - Quality only
- `/api/compliance-metrics` - Compliance only

## Real-World Example: E-Commerce Platform

```python
# 1. Register customer data asset
catalog = get_catalog()
customer_asset = DataAssetMetadata(
    asset_id="customers",
    name="Customer Database",
    asset_type="TABLE",
    layer="silver",
    platform="postgres",
    location="postgres://prod/customers",
    owner="data_team@company.com",
    owner_team="Data Engineering",
    tags=["customers", "pii", "core"],
    classification="RESTRICTED",
    contains_pii=True,
    pii_columns=["email", "phone", "address"]
)
catalog.register_asset(customer_asset)

# 2. Register derived tables (gold layer)
recommendations_asset = DataAssetMetadata(
    asset_id="customer_recommendations",
    name="Product Recommendations",
    asset_type="TABLE",
    layer="gold",
    platform="postgres",
    owner="ml_team@company.com",
    tags=["recommendations", "ml", "personalization"],
    classification="INTERNAL"
)
catalog.register_asset(recommendations_asset)

# 3. Track lineage: customer → recommendations
lineage = get_lineage_tracker()
lineage.record_lineage(
    source_asset="customers",
    target_asset="customer_recommendations",
    transformation_job="recommendation_engine",
    operation_type="ml_model"
)

# 4. Monitor quality
quality = get_quality_monitor()
quality.check_freshness("customers", last_updated, 6)  # Update every 6h
quality.check_completeness("customer_recommendations", 100000, 5)  # 100k records

# 5. Set GDPR retention (1 year for customer data)
compliance = get_compliance_tracker()
compliance.create_retention_policy(
    asset_id="customers",
    framework="gdpr",
    retention_days=365
)

# 6. Grant team access
access = get_access_manager()
access.grant_role("ml_engineer@company.com", "developer")

# 7. Search from UI/API
# GET /search?query=customer
# GET /assets/customers/lineage
# GET /assets/customer_recommendations/similar
```

## Troubleshooting

### "Module not found"
```bash
# Make sure you're importing correctly
from governance_layer.config.governance_config import governance_config
# ✗ Wrong: from config.governance_config import ...
# ✓ Right: from governance_layer.config.governance_config import ...
```

### "Assets not showing up"
```python
# Check if catalog is enabled
from governance_layer.config.governance_config import governance_config
print(governance_config.catalog.enable_catalog)

# Check storage path
print(governance_config.catalog.catalog_storage_path)

# Verify asset was registered
catalog = get_catalog()
asset = catalog.get_asset("my_first_asset")
print(asset)  # Should not be None
```

### "API key not working"
```python
# Recreate API key
access = get_access_manager()
new_key = access.create_api_key(
    owner="your@email.com",
    name="new_key",
    expiry_days=90
)
print(f"New key: {new_key}")

# Check if key is valid
key_id, key_secret = new_key.split(":")
is_valid = access.validate_api_key(key_id, key_secret)
print(f"Valid: {is_valid}")
```

## Next Steps

1. **Read the full documentation**: [GOVERNANCE_README.md](./GOVERNANCE_README.md)
2. **Run integration tests**: `python test_governance_layer.py`
3. **Integrate with your pipeline**: Import modules and add governance
4. **Start the APIs**: Run Discovery API and Dashboard
5. **Monitor governance**: Check dashboard regularly

## Architecture Overview

```
┌─────────────────────────────────────┐
│   Your Data Platform                │
├─────────────────────────────────────┤
│  Data Ingestion │ Processing │...   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   GOVERNANCE LAYER                  │
├─────────────────────────────────────┤
│  ┌─ Catalog ──┐  ┌─ Lineage ──┐    │
│  │ Metadata   │  │ Lineage    │    │
│  │ PII Track  │  │ Impact     │    │
│  └────────────┘  └────────────┘    │
│  ┌─ Quality ──┐  ┌─ Access ──┐     │
│  │ Freshness  │  │ RBAC       │    │
│  │ Completeness│ │ Audit Log  │    │
│  └────────────┘  └────────────┘    │
│  ┌─ Compliance ─┐ ┌─ Discovery ─┐  │
│  │ GDPR/CCPA    │ │ Search API  │  │
│  │ Retention    │ │ REST API    │  │
│  └──────────────┘ └─────────────┘  │
│     ┌─ Dashboard ─┐                │
│     │ Metrics     │                │
│     │ Monitoring  │                │
│     └─────────────┘                │
└─────────────────────────────────────┘
             │
             ▼
     ┌─────────────────┐
     │  Your Apps      │
     │  Dashboards     │
     │  Analytics      │
     └─────────────────┘
```

---

Happy governing! 🔐📊

For more info: See [GOVERNANCE_README.md](./GOVERNANCE_README.md)
