"""
Governance Layer Configuration
Manages data catalog, lineage, quality, compliance, and access control policies
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum
from pathlib import Path


class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"           # No restrictions
    INTERNAL = "internal"       # Internal use only
    CONFIDENTIAL = "confidential"  # Business sensitive
    RESTRICTED = "restricted"   # Highly sensitive (PII, financial)
    CLASSIFIED = "classified"   # Government classified


class ComplianceFramework(Enum):
    """Compliance frameworks"""
    GDPR = "gdpr"              # EU General Data Protection Regulation
    CCPA = "ccpa"              # California Consumer Privacy Act
    HIPAA = "hipaa"            # Health Insurance Portability and Accountability Act
    SOC2 = "soc2"              # Service Organization Control
    FERPA = "ferpa"            # Family Educational Rights and Privacy Act
    CUSTOM = "custom"          # Custom compliance rules


class DataOwnershipType(Enum):
    """Data ownership types"""
    INDIVIDUAL = "individual"
    TEAM = "team"
    DEPARTMENT = "department"


@dataclass
class CatalogConfig:
    """Data catalog configuration"""
    # Enable catalogs
    enable_catalog: bool = True
    # Catalog storage
    catalog_storage_path: str = "/workspaces/Data-Platform/governance_layer/catalog/data"
    # Auto-discovery
    auto_discover_tables: bool = True
    # Metadata versioning
    version_history: bool = True
    # Max catalog entries
    max_entries: int = 10000


@dataclass
class LineageConfig:
    """Data lineage configuration"""
    # Enable lineage tracking
    enable_lineage: bool = True
    # Track column-level lineage
    column_level_lineage: bool = True
    # Lineage storage
    lineage_storage_path: str = "/workspaces/Data-Platform/governance_layer/lineage/data"
    # Max lineage history
    max_history_days: int = 365
    # Impact analysis enabled
    enable_impact_analysis: bool = True


@dataclass
class QualityConfig:
    """Data quality configuration"""
    # Enable quality checks
    enable_quality_monitoring: bool = True
    # Quality storage
    quality_storage_path: str = "/workspaces/Data-Platform/governance_layer/quality/data"
    # SLA thresholds
    sla_freshness_hours: int = 24
    sla_completeness_percent: float = 95.0
    sla_accuracy_percent: float = 98.0
    # Anomaly detection
    enable_anomaly_detection: bool = True
    anomaly_sensitivity: str = "medium"  # low, medium, high
    # Quality rules engine
    enable_rules_engine: bool = True
    # Quality scorecard
    enable_scorecards: bool = True


@dataclass
class AccessControlConfig:
    """Access control configuration"""
    # Enable RBAC
    enable_rbac: bool = True
    # Access storage
    access_storage_path: str = "/workspaces/Data-Platform/governance_layer/access/data"
    # API key management
    enable_api_keys: bool = True
    api_key_expiry_days: int = 365
    # Audit logging
    enable_audit_logging: bool = True
    audit_retention_days: int = 730  # 2 years
    # Row-level security
    enable_row_level_security: bool = False


@dataclass
class ComplianceConfig:
    """Compliance configuration"""
    # Enable compliance tracking
    enable_compliance: bool = True
    # Compliance storage
    compliance_storage_path: str = "/workspaces/Data-Platform/governance_layer/compliance/data"
    # Frameworks to track
    frameworks: List[str] = field(default_factory=lambda: ["gdpr", "ccpa", "soc2"])
    # Data retention
    retention_storage_path: str = "/workspaces/Data-Platform/governance_layer/compliance/retention"
    # Right-to-be-forgotten
    enable_rtbf: bool = True
    # Data deletion audit
    track_deletion_audit: bool = True
    # Encryption at rest
    enable_encryption: bool = True
    encryption_algorithm: str = "AES-256"


@dataclass
class DiscoveryConfig:
    """Data discovery configuration"""
    # Enable discovery API
    enable_discovery: bool = True
    # Full-text search
    enable_full_text_search: bool = True
    # Search storage
    search_index_path: str = "/workspaces/Data-Platform/governance_layer/discovery/index"
    # Auto-generated documentation
    enable_auto_docs: bool = True
    # Data relationships
    enable_relationships: bool = True
    # Recommendations
    enable_recommendations: bool = True


@dataclass
class DashboardConfig:
    """Governance dashboard configuration"""
    # Enable dashboard
    enable_dashboard: bool = True
    # Dashboard port
    dashboard_port: int = 8889
    # Refresh interval (seconds)
    refresh_interval: int = 300  # 5 minutes
    # Metrics tracked
    track_metrics: List[str] = field(default_factory=lambda: [
        "table_freshness",
        "data_quality",
        "access_patterns",
        "compliance_status",
        "storage_usage",
        "user_activity"
    ])
    # Notifications
    enable_notifications: bool = True
    notification_channels: List[str] = field(default_factory=lambda: ["email"])


@dataclass
class DataStewardConfig:
    """Data steward configuration"""
    # Enable stewardship
    enable_stewardship: bool = True
    # Steward roles
    steward_roles: List[str] = field(default_factory=lambda: [
        "data_owner",
        "data_steward",
        "quality_champion",
        "compliance_officer"
    ])
    # Contact management
    enable_contact_management: bool = True
    # Escalation policies
    enable_escalation: bool = True
    # SLA tracking
    enable_sla_tracking: bool = True


class GovernanceConfig:
    """Main Governance Configuration Manager"""

    def __init__(self):
        """Initialize governance configuration"""
        # Catalog config
        self.catalog = CatalogConfig(
            catalog_storage_path=os.getenv('CATALOG_STORAGE_PATH',
                '/workspaces/Data-Platform/governance_layer/catalog/data')
        )

        # Lineage config
        self.lineage = LineageConfig(
            lineage_storage_path=os.getenv('LINEAGE_STORAGE_PATH',
                '/workspaces/Data-Platform/governance_layer/lineage/data')
        )

        # Quality config
        self.quality = QualityConfig(
            quality_storage_path=os.getenv('QUALITY_STORAGE_PATH',
                '/workspaces/Data-Platform/governance_layer/quality/data'),
            sla_freshness_hours=int(os.getenv('SLA_FRESHNESS_HOURS', '24')),
            sla_completeness_percent=float(os.getenv('SLA_COMPLETENESS_PERCENT', '95.0'))
        )

        # Access control config
        self.access = AccessControlConfig(
            access_storage_path=os.getenv('ACCESS_STORAGE_PATH',
                '/workspaces/Data-Platform/governance_layer/access/data'),
            api_key_expiry_days=int(os.getenv('API_KEY_EXPIRY_DAYS', '365'))
        )

        # Compliance config
        self.compliance = ComplianceConfig(
            compliance_storage_path=os.getenv('COMPLIANCE_STORAGE_PATH',
                '/workspaces/Data-Platform/governance_layer/compliance/data'),
            enable_encryption=os.getenv('ENABLE_ENCRYPTION', 'true').lower() == 'true'
        )

        # Discovery config
        self.discovery = DiscoveryConfig(
            search_index_path=os.getenv('SEARCH_INDEX_PATH',
                '/workspaces/Data-Platform/governance_layer/discovery/index')
        )

        # Dashboard config
        self.dashboard = DashboardConfig(
            dashboard_port=int(os.getenv('DASHBOARD_PORT', '8889')),
            refresh_interval=int(os.getenv('DASHBOARD_REFRESH_INTERVAL', '300'))
        )

        # Steward config
        self.steward = DataStewardConfig()

        # Log level
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # Create storage directories
        self._create_storage_directories()

    def _create_storage_directories(self):
        """Create all required storage directories"""
        paths = [
            self.catalog.catalog_storage_path,
            self.lineage.lineage_storage_path,
            self.quality.quality_storage_path,
            self.access.access_storage_path,
            self.compliance.compliance_storage_path,
            self.compliance.retention_storage_path,
            self.discovery.search_index_path,
        ]
        
        for path in paths:
            Path(path).mkdir(parents=True, exist_ok=True)

    def get_config_dict(self) -> Dict:
        """Get configuration as dictionary"""
        return {
            'catalog': self.catalog.__dict__,
            'lineage': self.lineage.__dict__,
            'quality': self.quality.__dict__,
            'access': self.access.__dict__,
            'compliance': self.compliance.__dict__,
            'discovery': self.discovery.__dict__,
            'dashboard': self.dashboard.__dict__,
            'steward': self.steward.__dict__,
            'log_level': self.log_level
        }


# Global configuration instance
governance_config = GovernanceConfig()
