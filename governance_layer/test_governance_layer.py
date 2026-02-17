"""
Governance Layer Integration Test & Examples
Demonstrates usage of all governance components
"""

import json
from datetime import datetime, timedelta

# Import all governance modules
from config.governance_config import governance_config
from catalog.data_catalog import get_catalog, DataAssetMetadata, ColumnMetadata
from lineage.lineage_tracker import get_lineage_tracker
from quality.quality_monitor import get_quality_monitor
from access.access_control import get_access_manager, UserRole
from compliance.compliance_tracker import get_compliance_tracker, ComplianceFramework
from discovery.discovery_api import get_discovery_api
from dashboard.governance_dashboard import get_governance_dashboard


def test_catalog_operations():
    """Test data catalog operations"""
    print("\n" + "="*60)
    print("TESTING DATA CATALOG")
    print("="*60)
    
    catalog = get_catalog()
    
    # Create sample asset
    asset = DataAssetMetadata(
        asset_id="customer_bronze",
        name="Customer Data (Bronze)",
        asset_type="TABLE",
        layer="bronze",
        platform="parquet",
        location="/data/bronze/customers",
        owner="data_owner@company.com",
        owner_email="data_owner@company.com",
        owner_team="Data Engineering",
        description="Raw customer data from source systems",
        tags=["customers", "raw", "pii"],
        classification="RESTRICTED",
        contains_pii=True,
        pii_columns=["email", "phone", "ssn"]
    )
    
    # Register asset
    asset_id = catalog.register_asset(asset)
    print(f"✓ Registered asset: {asset_id}")
    
    # Search assets
    results = catalog.search_assets("customer")
    print(f"✓ Search found {len(results)} assets")
    
    # Get assets by tag
    tagged = catalog.get_assets_by_tag("pii")
    print(f"✓ Found {len(tagged)} PII assets")
    
    # Update asset
    catalog.update_asset(asset_id, {"description": "Updated description"})
    print(f"✓ Updated asset metadata")
    
    # Get catalog report
    report = catalog.get_catalog_report()
    print(f"✓ Catalog report: {report.get('total_assets')} total assets")
    
    return asset_id


def test_lineage_operations(asset_id):
    """Test data lineage tracking"""
    print("\n" + "="*60)
    print("TESTING DATA LINEAGE")
    print("="*60)
    
    lineage = get_lineage_tracker()
    
    # Create another asset for lineage
    target_asset = "customer_silver"
    
    # Record lineage
    edge_id = lineage.record_lineage(
        source_asset=asset_id,
        target_asset=target_asset,
        transformation_job="customer_etl_job",
        operation_type="transformation",
        created_by="etl_user@company.com"
    )
    print(f"✓ Recorded lineage edge: {edge_id}")
    
    # Get upstream lineage
    upstream = lineage.get_upstream_lineage(target_asset, depth=3)
    print(f"✓ Upstream lineage: {len(upstream.get('all_sources', []))} sources")
    
    # Get impact analysis
    impact = lineage.get_impact_analysis(asset_id)
    print(f"✓ Impact analysis: {impact.get('impact_level')} impact level")
    
    # Get lineage report
    report = lineage.get_lineage_report()
    print(f"✓ Lineage report: {report.get('edges_count')} total edges")
    
    return target_asset


def test_quality_operations(asset_id):
    """Test quality monitoring"""
    print("\n" + "="*60)
    print("TESTING DATA QUALITY")
    print("="*60)
    
    quality = get_quality_monitor()
    
    # Register quality checks
    freshness_check = quality.register_quality_check(
        asset_id=asset_id,
        check_type="freshness",
        metric_name="last_update_age_hours",
        threshold=24
    )
    print(f"✓ Registered freshness check: {freshness_check}")
    
    completeness_check = quality.register_quality_check(
        asset_id=asset_id,
        check_type="completeness",
        metric_name="null_percentage",
        threshold=95
    )
    print(f"✓ Registered completeness check: {completeness_check}")
    
    # Execute checks
    quality.execute_quality_check(freshness_check, 12)
    quality.execute_quality_check(completeness_check, 98)
    print(f"✓ Executed quality checks")
    
    # Check freshness
    is_fresh = quality.check_freshness(
        asset_id=asset_id,
        last_updated=datetime.now().isoformat(),
        expected_hours=24
    )
    print(f"✓ Freshness check: {is_fresh}")
    
    # Check completeness
    completeness = quality.check_completeness(
        asset_id=asset_id,
        total_records=1000,
        null_records=20
    )
    print(f"✓ Completeness: {completeness:.1f}%")
    
    # Detect anomalies
    anomaly = quality.detect_anomalies(
        asset_id=asset_id,
        metric_name="record_count",
        current_value=1000
    )
    print(f"✓ Anomaly detection: is_anomaly={anomaly.is_anomaly}")
    
    # Calculate quality score
    scorecard = quality.calculate_quality_score(asset_id)
    print(f"✓ Quality scorecard: {scorecard.overall_score:.1f}/100 ({scorecard.status})")
    
    # Check SLA
    violations = quality.enforce_sla(asset_id)
    print(f"✓ SLA check: {len(violations)} violations")
    
    # Get quality report
    report = quality.get_quality_report(days=30)
    print(f"✓ Quality report: {report.get('total_assets_monitored')} monitored assets")


def test_access_control_operations():
    """Test access control and RBAC"""
    print("\n" + "="*60)
    print("TESTING ACCESS CONTROL")
    print("="*60)
    
    access = get_access_manager()
    
    # Grant roles
    access.grant_role("alice@company.com", "data_owner")
    access.grant_role("bob@company.com", "analyst")
    print(f"✓ Granted roles to users")
    
    # Create API key
    api_key = access.create_api_key(
        owner="alice@company.com",
        name="ML_Pipeline_Key",
        scopes=["read", "write"],
        expiry_days=90
    )
    print(f"✓ Created API key: {api_key[:20]}...")
    
    # Check permissions
    has_perm = access.check_permission(
        user="alice@company.com",
        action="write",
        resource_type="catalog"
    )
    print(f"✓ Permission check: {has_perm}")
    
    # Log audit event
    log_id = access.log_audit_event(
        user="alice@company.com",
        action="register_asset",
        resource_type="catalog",
        resource_id="customer_bronze",
        status="success"
    )
    print(f"✓ Logged audit event: {log_id}")
    
    # Get audit logs
    logs = access.get_audit_logs(user="alice@company.com", days=30)
    print(f"✓ Retrieved {len(logs)} audit logs")
    
    # Get access report
    report = access.get_access_report()
    print(f"✓ Access report: {report.get('api_keys', {}).get('active')} active API keys")


def test_compliance_operations():
    """Test compliance and retention management"""
    print("\n" + "="*60)
    print("TESTING COMPLIANCE")
    print("="*60)
    
    compliance = get_compliance_tracker()
    
    # Create retention policy
    policy_id = compliance.create_retention_policy(
        asset_id="customer_bronze",
        framework="gdpr",
        retention_days=365,
        purge_after_days=730,
        description="GDPR compliant retention for customer data"
    )
    print(f"✓ Created retention policy: {policy_id}")
    
    # Apply retention policy
    result = compliance.apply_retention_policy("customer_bronze")
    print(f"✓ Applied retention policy: {result.get('message')}")
    
    # Submit RTBF request
    rtbf_id = compliance.submit_rtbf_request(
        data_subject_id="subject_12345",
        asset_ids=["customer_bronze", "customer_silver"],
        requested_by="privacy_officer@company.com",
        reason="Data subject exercised right to be forgotten"
    )
    print(f"✓ Submitted RTBF request: {rtbf_id}")
    
    # Process RTBF request
    rtbf_result = compliance.process_rtbf_request(rtbf_id)
    print(f"✓ Processed RTBF: {rtbf_result.get('assets_processed')} assets processed")
    
    # Assess compliance
    assets = [
        {"id": "customer_bronze", "contains_pii": True, "encryption_enabled": True, "owner": "data_owner@company.com"},
        {"id": "customer_silver", "contains_pii": True, "encryption_enabled": True, "owner": "data_owner@company.com"}
    ]
    report = compliance.assess_compliance("gdpr", assets)
    print(f"✓ Compliance assessment: {report.overall_status} - {report.compliant_assets}/{len(assets)} compliant")
    
    # Get compliance summary
    summary = compliance.generate_compliance_summary()
    print(f"✓ Compliance summary: {summary.get('overall_status')}")


def test_discovery_api_operations():
    """Test data discovery API"""
    print("\n" + "="*60)
    print("TESTING DATA DISCOVERY API")
    print("="*60)
    
    discovery = get_discovery_api()
    
    if discovery.app:
        print(f"✓ Discovery API initialized on port {discovery.port}")
        
        # Export API spec
        spec_path = "/tmp/discovery_api_spec.json"
        discovery.export_api_spec(spec_path)
        print(f"✓ Exported API specification to {spec_path}")
    else:
        print("⚠ FastAPI not available - skipping API tests")


def test_governance_dashboard():
    """Test governance dashboard"""
    print("\n" + "="*60)
    print("TESTING GOVERNANCE DASHBOARD")
    print("="*60)
    
    dashboard = get_governance_dashboard()
    
    # Get dashboard metrics
    metrics = dashboard.get_dashboard_metrics()
    print(f"✓ Dashboard metrics collected")
    print(f"  - Overall status: {metrics.get('overall_status')}")
    print(f"  - Catalog assets: {metrics.get('catalog', {}).get('total_assets')}")
    print(f"  - Quality score: {metrics.get('quality', {}).get('quality_percentage'):.1f}%")
    print(f"  - Compliance: {metrics.get('compliance', {}).get('overall_status')}")


def print_configuration():
    """Print governance configuration"""
    print("\n" + "="*60)
    print("GOVERNANCE CONFIGURATION")
    print("="*60)
    
    config = governance_config
    
    print(f"Catalog enabled: {config.catalog.enable_catalog}")
    print(f"Lineage enabled: {config.lineage.enable_lineage}")
    print(f"Quality monitoring enabled: {config.quality.enable_quality_monitoring}")
    print(f"Access control enabled: {config.access.enable_rbac}")
    print(f"Compliance enabled: {config.compliance.enable_compliance}")
    print(f"Discovery enabled: {config.discovery.enable_discovery}")
    print(f"Dashboard enabled: {config.dashboard.enable_dashboard}")
    
    print(f"\nStorage paths:")
    print(f"  Catalog: {config.catalog.catalog_storage_path}")
    print(f"  Lineage: {config.lineage.lineage_storage_path}")
    print(f"  Quality: {config.quality.quality_storage_path}")
    print(f"  Access: {config.access.access_storage_path}")
    print(f"  Compliance: {config.compliance.retention_storage_path}")


def export_governance_reports():
    """Export all governance reports"""
    print("\n" + "="*60)
    print("EXPORTING GOVERNANCE REPORTS")
    print("="*60)
    
    catalog = get_catalog()
    lineage = get_lineage_tracker()
    quality = get_quality_monitor()
    access_mgr = get_access_manager()
    compliance = get_compliance_tracker()
    
    exports = {
        "catalog": "/tmp/governance_catalog_report.json",
        "lineage": "/tmp/governance_lineage_report.json",
        "quality": "/tmp/governance_quality_report.json",
        "compliance": "/tmp/governance_compliance_report.json"
    }
    
    catalog.export_catalog(exports["catalog"])
    print(f"✓ Exported catalog to {exports['catalog']}")
    
    lineage.export_lineage(exports["lineage"])
    print(f"✓ Exported lineage to {exports['lineage']}")
    
    quality.export_quality_data(exports["quality"])
    print(f"✓ Exported quality data to {exports['quality']}")
    
    compliance.export_compliance_data(exports["compliance"])
    print(f"✓ Exported compliance data to {exports['compliance']}")
    
    access_mgr.export_audit_logs("/tmp/governance_audit_logs.json")
    print(f"✓ Exported audit logs to /tmp/governance_audit_logs.json")


def main():
    """Run all governance tests"""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  GOVERNANCE LAYER - INTEGRATION TEST & EXAMPLES".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    try:
        # Print configuration
        print_configuration()
        
        # Test each component
        asset_id = test_catalog_operations()
        target_asset = test_lineage_operations(asset_id)
        test_quality_operations(asset_id)
        test_access_control_operations()
        test_compliance_operations()
        test_discovery_api_operations()
        test_governance_dashboard()
        
        # Export reports
        export_governance_reports()
        
        # Final summary
        print("\n" + "="*60)
        print("✓ ALL GOVERNANCE TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nGovernance layer is ready for use!")
        print("\nNext steps:")
        print("1. Start the Discovery API: python -c \"from discovery.discovery_api import get_discovery_api; get_discovery_api().start()\"")
        print("2. Start the Dashboard: python -c \"from dashboard.governance_dashboard import get_governance_dashboard; get_governance_dashboard().start()\"")
        print("3. Import governance modules in your applications")
        print("4. Integrate with your data pipelines")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
