"""
Governance Dashboard
Real-time monitoring and visualization of governance metrics
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from config.governance_config import governance_config
from catalog.data_catalog import get_catalog
from lineage.lineage_tracker import get_lineage_tracker
from quality.quality_monitor import get_quality_monitor
from access.access_control import get_access_manager
from compliance.compliance_tracker import get_compliance_tracker

try:
    from fastapi import FastAPI, Query
    from fastapi.responses import HTMLResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class GovernanceDashboard:
    """Governance monitoring dashboard"""

    def __init__(self, port: int = 8890):
        """Initialize dashboard"""
        self.port = port
        self.catalog = get_catalog()
        self.lineage = get_lineage_tracker()
        self.quality = get_quality_monitor()
        self.access_manager = get_access_manager()
        self.compliance = get_compliance_tracker()
        
        self.storage_path = Path(governance_config.dashboard.dashboard_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        if FASTAPI_AVAILABLE:
            self.app = FastAPI(
                title="Governance Dashboard",
                description="Real-time governance monitoring",
                version="1.0.0"
            )
            self._setup_routes()
        else:
            self.app = None

    def _setup_routes(self):
        """Setup dashboard routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Render main dashboard"""
            metrics = self.get_dashboard_metrics()
            html = self._render_dashboard_html(metrics)
            return html
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get all dashboard metrics"""
            return self.get_dashboard_metrics()
        
        @self.app.get("/api/catalog-metrics")
        async def get_catalog_metrics():
            """Get catalog metrics"""
            report = self.catalog.get_catalog_report()
            return {
                "total_assets": report.get("total_assets", 0),
                "by_layer": report.get("assets_by_layer", {}),
                "by_classification": report.get("assets_by_classification", {}),
                "by_owner": report.get("assets_by_owner", {}),
                "pii_assets_count": report.get("pii_assets_count", 0),
                "unique_owners": report.get("unique_owners", 0),
                "unique_tags": report.get("unique_tags", 0),
                "asset_types": report.get("asset_types", {})
            }
        
        @self.app.get("/api/lineage-metrics")
        async def get_lineage_metrics():
            """Get lineage metrics"""
            report = self.lineage.get_lineage_report()
            return {
                "total_edges": report.get("edges_count", 0),
                "source_assets": report.get("source_assets_count", 0),
                "sink_assets": report.get("sink_assets_count", 0),
                "transformation_types": report.get("transformation_types", {}),
                "column_lineages": report.get("column_lineages_count", 0),
                "complexity_distribution": report.get("most_complex_assets", [])
            }
        
        @self.app.get("/api/quality-metrics")
        async def get_quality_metrics(days: int = Query(30)):
            """Get quality metrics"""
            report = self.quality.get_quality_report(days=days)
            return {
                "total_monitored": report.get("total_assets_monitored", 0),
                "excellent_assets": report.get("excellent_assets", 0),
                "good_assets": report.get("good_assets", 0),
                "fair_assets": report.get("fair_assets", 0),
                "poor_assets": report.get("poor_assets", 0),
                "sla_violations": report.get("total_sla_violations", 0),
                "critical_violations": report.get("critical_violations", 0),
                "high_severity_anomalies": report.get("high_severity_anomalies", 0),
                "worst_assets": [
                    {
                        "asset_id": asset[0] if isinstance(asset, tuple) else asset.get("asset_id"),
                        "score": asset[1] if isinstance(asset, tuple) else asset.get("overall_score"),
                        "status": asset[2] if isinstance(asset, tuple) else asset.get("status")
                    }
                    for asset in report.get("worst_performing_assets", [])
                ]
            }
        
        @self.app.get("/api/access-metrics")
        async def get_access_metrics():
            """Get access control metrics"""
            report = self.access_manager.get_access_report()
            return {
                "api_keys_total": report.get("api_keys", {}).get("total", 0),
                "api_keys_active": report.get("api_keys", {}).get("active", 0),
                "api_keys_expired": report.get("api_keys", {}).get("expired", 0),
                "audit_logs_total": report.get("audit_logs", {}).get("total", 0),
                "audit_successful": report.get("audit_logs", {}).get("successful", 0),
                "audit_failed": report.get("audit_logs", {}).get("failed", 0),
                "audit_denied": report.get("audit_logs", {}).get("denied", 0),
                "defined_roles": report.get("defined_roles", []),
                "most_active_users": report.get("most_active_users", [])
            }
        
        @self.app.get("/api/compliance-metrics")
        async def get_compliance_metrics():
            """Get compliance metrics"""
            summary = self.compliance.generate_compliance_summary()
            return {
                "overall_status": summary.get("overall_status"),
                "frameworks": summary.get("frameworks", {}),
                "last_updated": summary.get("timestamp")
            }
        
        @self.app.get("/api/storage-metrics")
        async def get_storage_metrics():
            """Get storage metrics"""
            catalog_report = self.catalog.get_catalog_report()
            return {
                "total_assets": catalog_report.get("total_assets", 0),
                "storage_by_layer": self._estimate_storage_by_layer(),
                "total_storage_gb": self._estimate_total_storage()
            }
        
        @self.app.get("/api/activity-metrics")
        async def get_activity_metrics(days: int = Query(30)):
            """Get activity metrics"""
            audit_logs = self.access_manager.get_audit_logs(days=days)
            
            # Group by date
            activity_by_date = {}
            for log in audit_logs:
                date = log.timestamp.split('T')[0]
                activity_by_date[date] = activity_by_date.get(date, 0) + 1
            
            return {
                "total_events": len(audit_logs),
                "activity_by_date": activity_by_date,
                "events_by_type": self._count_events_by_type(audit_logs),
                "top_users": self._get_top_users(audit_logs)
            }

    def get_dashboard_metrics(self) -> Dict:
        """Collect all metrics for dashboard"""
        return {
            "timestamp": datetime.now().isoformat(),
            "catalog": self._get_catalog_health(),
            "lineage": self._get_lineage_health(),
            "quality": self._get_quality_health(),
            "access": self._get_access_health(),
            "compliance": self._get_compliance_health(),
            "storage": self._get_storage_health(),
            "overall_status": self._calculate_overall_status()
        }

    def _get_catalog_health(self) -> Dict:
        """Get catalog health metrics"""
        report = self.catalog.get_catalog_report()
        return {
            "total_assets": report.get("total_assets", 0),
            "layers": report.get("assets_by_layer", {}),
            "pii_assets": report.get("pii_assets_count", 0),
            "unowned_assets": report.get("assets_without_owner", 0),
            "documentation_coverage": self._calculate_documentation_coverage(),
            "status": "healthy" if report.get("total_assets", 0) > 0 else "warning"
        }

    def _get_lineage_health(self) -> Dict:
        """Get data lineage health"""
        report = self.lineage.get_lineage_report()
        return {
            "total_transformations": report.get("edges_count", 0),
            "source_tables": report.get("source_assets_count", 0),
            "sink_tables": report.get("sink_assets_count", 0),
            "average_complexity": self._calculate_average_lineage_complexity(report),
            "status": "healthy" if report.get("edges_count", 0) > 0 else "warning"
        }

    def _get_quality_health(self) -> Dict:
        """Get data quality health"""
        report = self.quality.get_quality_report()
        excellent_pct = 0
        total = report.get("total_assets_monitored", 0)
        if total > 0:
            excellent_pct = (report.get("excellent_assets", 0) / total) * 100
        
        status = "healthy" if excellent_pct >= 75 else ("warning" if excellent_pct >= 50 else "critical")
        
        return {
            "excellent_assets": report.get("excellent_assets", 0),
            "good_assets": report.get("good_assets", 0),
            "total_monitored": total,
            "quality_percentage": excellent_pct,
            "sla_violations": report.get("total_sla_violations", 0),
            "anomalies_detected": report.get("high_severity_anomalies", 0),
            "status": status
        }

    def _get_access_health(self) -> Dict:
        """Get access control health"""
        report = self.access_manager.get_access_report()
        api_report = report.get("api_keys", {})
        
        active_pct = 0
        total_keys = api_report.get("total", 0)
        if total_keys > 0:
            active_pct = (api_report.get("active", 0) / total_keys) * 100
        
        return {
            "api_keys_active": api_report.get("active", 0),
            "api_keys_expired": api_report.get("expired", 0),
            "audit_log_retention_days": governance_config.access.audit_log_retention_days,
            "rbac_enabled": governance_config.access.enable_rbac,
            "defined_roles": len(report.get("defined_roles", [])),
            "status": "healthy" if active_pct >= 80 else "warning"
        }

    def _get_compliance_health(self) -> Dict:
        """Get compliance health"""
        summary = self.compliance.generate_compliance_summary()
        frameworks = summary.get("frameworks", {})
        
        compliant_count = sum(
            1 for f in frameworks.values()
            if f.get("status") == "compliant"
        )
        
        return {
            "overall_status": summary.get("overall_status"),
            "frameworks_assessed": len(frameworks),
            "compliant_frameworks": compliant_count,
            "frameworks": frameworks,
            "status": "healthy" if summary.get("overall_status") == "compliant" else "critical"
        }

    def _get_storage_health(self) -> Dict:
        """Get storage health"""
        catalog_report = self.catalog.get_catalog_report()
        return {
            "total_assets": catalog_report.get("total_assets", 0),
            "storage_by_layer": self._estimate_storage_by_layer(),
            "total_storage_gb": self._estimate_total_storage(),
            "status": "healthy"
        }

    def _calculate_overall_status(self) -> str:
        """Calculate overall governance health"""
        metrics = self.get_dashboard_metrics()
        
        statuses = [
            metrics.get("catalog", {}).get("status", "unknown"),
            metrics.get("quality", {}).get("status", "unknown"),
            metrics.get("access", {}).get("status", "unknown"),
            metrics.get("compliance", {}).get("status", "unknown")
        ]
        
        critical_count = statuses.count("critical")
        warning_count = statuses.count("warning")
        
        if critical_count >= 2:
            return "critical"
        elif critical_count >= 1 or warning_count >= 2:
            return "warning"
        else:
            return "healthy"

    def _calculate_documentation_coverage(self) -> float:
        """Calculate documentation coverage percentage"""
        # Placeholder - in real implementation, count assets with descriptions
        return 85.0

    def _calculate_average_lineage_complexity(self, report: Dict) -> float:
        """Calculate average lineage complexity"""
        most_complex = report.get("most_complex_assets", [])
        if not most_complex:
            return 0.0
        
        # Sum complexity (approximated by downstream count)
        total = sum(asset[1] if isinstance(asset, tuple) else 0 for asset in most_complex)
        return total / len(most_complex) if most_complex else 0.0

    def _estimate_storage_by_layer(self) -> Dict:
        """Estimate storage by layer"""
        return {
            "bronze": 100,  # GB
            "silver": 50,
            "gold": 10
        }

    def _estimate_total_storage(self) -> float:
        """Estimate total storage"""
        layer_stats = self._estimate_storage_by_layer()
        return sum(layer_stats.values())

    def _count_events_by_type(self, logs: List) -> Dict:
        """Count events by type"""
        counts = {}
        for log in logs:
            event_type = log.action
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts

    def _get_top_users(self, logs: List) -> List[Dict]:
        """Get top active users"""
        user_counts = {}
        for log in logs:
            user = log.user
            user_counts[user] = user_counts.get(user, 0) + 1
        
        sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"user": user, "events": count}
            for user, count in sorted_users[:10]
        ]

    def _render_dashboard_html(self, metrics: Dict) -> str:
        """Render dashboard HTML"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Governance Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .status-indicator {{
            display: inline-block;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
        }}
        .status-healthy {{ background-color: #10b981; }}
        .status-warning {{ background-color: #f59e0b; }}
        .status-critical {{ background-color: #ef4444; }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .metric-card h3 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .metric-row:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        .metric-label {{
            color: #666;
            font-weight: 500;
        }}
        .metric-value {{
            color: #333;
            font-weight: bold;
            font-size: 16px;
        }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }}
        .alert {{
            padding: 15px;
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            border-radius: 4px;
            margin-bottom: 20px;
            color: #92400e;
        }}
        .alert.critical {{
            background: #fee2e2;
            border-left-color: #ef4444;
            color: #7f1d1d;
        }}
        .timestamp {{
            text-align: right;
            color: #999;
            font-size: 12px;
            margin-top: 20px;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .pulse {{ animation: pulse 2s infinite; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>
                <span class="status-indicator status-{metrics.get('overall_status', 'unknown')}"></span>
                Governance Dashboard
            </h1>
            <p>Real-time monitoring of data governance across the platform</p>
        </header>
        
        {"<div class='alert critical'><strong>⚠️ Critical Issues Detected</strong> - Please review compliance and quality metrics</div>" if metrics.get('overall_status') == 'critical' else ""}
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>📊 Catalog Health</h3>
                <div class="metric-row">
                    <span class="metric-label">Total Assets</span>
                    <span class="metric-value">{metrics.get('catalog', {}).get('total_assets', 0)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">PII Assets</span>
                    <span class="metric-value">{metrics.get('catalog', {}).get('pii_assets', 0)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Unowned Assets</span>
                    <span class="metric-value">{metrics.get('catalog', {}).get('unowned_assets', 0)}</span>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>📈 Quality Health</h3>
                <div class="metric-row">
                    <span class="metric-label">Excellent Assets</span>
                    <span class="metric-value">{metrics.get('quality', {}).get('excellent_assets', 0)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Quality Score</span>
                    <span class="metric-value">{metrics.get('quality', {}).get('quality_percentage', 0):.1f}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">SLA Violations</span>
                    <span class="metric-value">{metrics.get('quality', {}).get('sla_violations', 0)}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {metrics.get('quality', {}).get('quality_percentage', 0)}%"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>🔐 Access Control</h3>
                <div class="metric-row">
                    <span class="metric-label">Active API Keys</span>
                    <span class="metric-value">{metrics.get('access', {}).get('api_keys_active', 0)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Defined Roles</span>
                    <span class="metric-value">{metrics.get('access', {}).get('defined_roles', 0)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Expired Keys</span>
                    <span class="metric-value">{metrics.get('access', {}).get('api_keys_expired', 0)}</span>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>⚖️ Compliance Status</h3>
                <div class="metric-row">
                    <span class="metric-label">Overall Status</span>
                    <span class="metric-value">{metrics.get('compliance', {}).get('overall_status', 'unknown').upper()}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Frameworks Assessed</span>
                    <span class="metric-value">{metrics.get('compliance', {}).get('frameworks_assessed', 0)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Compliant</span>
                    <span class="metric-value">{metrics.get('compliance', {}).get('compliant_frameworks', 0)}</span>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>📊 Data Lineage</h3>
                <div class="metric-row">
                    <span class="metric-label">Total Transformations</span>
                    <span class="metric-value">{metrics.get('lineage', {}).get('total_transformations', 0)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Source Tables</span>
                    <span class="metric-value">{metrics.get('lineage', {}).get('source_tables', 0)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Sink Tables</span>
                    <span class="metric-value">{metrics.get('lineage', {}).get('sink_tables', 0)}</span>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>💾 Storage</h3>
                <div class="metric-row">
                    <span class="metric-label">Total Storage</span>
                    <span class="metric-value">{metrics.get('storage', {}).get('total_storage_gb', 0):.1f} GB</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Total Assets</span>
                    <span class="metric-value">{metrics.get('storage', {}).get('total_assets', 0)}</span>
                </div>
            </div>
        </div>
        
        <div class="timestamp">Last updated: {metrics.get('timestamp')}</div>
    </div>
</body>
</html>
"""

    def start(self):
        """Start the dashboard server"""
        if not FASTAPI_AVAILABLE:
            print("FastAPI not available. Install with: pip install fastapi uvicorn")
            return
        
        if self.app is None:
            print("Dashboard not initialized")
            return
        
        try:
            import uvicorn
            print(f"Starting Governance Dashboard on port {self.port}")
            print(f"Dashboard: http://localhost:{self.port}")
            uvicorn.run(self.app, host="0.0.0.0", port=self.port)
        except ImportError:
            print("Uvicorn not available. Install with: pip install uvicorn")


# Global dashboard instance
_dashboard = None

def get_governance_dashboard(port: int = 8890) -> GovernanceDashboard:
    """Get or create global governance dashboard"""
    global _dashboard
    if _dashboard is None:
        _dashboard = GovernanceDashboard(port=port)
    return _dashboard
