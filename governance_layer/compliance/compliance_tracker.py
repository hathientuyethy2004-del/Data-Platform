"""
Compliance & Data Retention Management
Handles GDPR/CCPA compliance, retention policies, and right-to-be-forgotten (RTBF) processing
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from config.governance_config import governance_config


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    GDPR = "gdpr"           # EU General Data Protection Regulation
    CCPA = "ccpa"           # California Consumer Privacy Act
    HIPAA = "hipaa"         # Health Insurance Portability and Accountability Act
    SOC2 = "soc2"           # Service Organization Control 2
    FERPA = "ferpa"         # Family Educational Rights and Privacy Act
    CUSTOM = "custom"       # Custom compliance rules


@dataclass
class RetentionPolicy:
    """Data retention policy"""
    policy_id: str
    asset_id: str
    framework: str
    retention_days: int  # How long to keep data
    purge_after_days: int  # When to purge/delete
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""
    description: str = ""


@dataclass
class RTBFRequest:
    """Right-to-be-forgotten request"""
    request_id: str
    data_subject_id: str  # The person whose data should be deleted
    asset_ids: List[str]  # Assets containing their data
    requested_at: str
    status: str  # pending, processing, completed, rejected
    reason: str = ""
    requested_by: str = ""
    completed_at: str = ""
    assets_processed: List[str] = None
    error_details: str = ""


@dataclass
class ComplianceReport:
    """Compliance assessment report"""
    report_id: str
    framework: str
    generated_at: str
    overall_status: str  # compliant, non_compliant, partial
    total_assets: int
    scanned_assets: int
    compliant_assets: int
    issues: List[Dict] = None
    recommendations: List[str] = None
    assets_needing_attention: List[str] = None


@dataclass
class DeletionAudit:
    """Track data deletion for compliance"""
    deletion_id: str
    asset_id: str
    deletion_reason: str
    deleted_at: str
    deleted_by: str
    records_deleted: int
    rtbf_request_id: str = ""
    verification: Dict = None  # Hash/checksum for verification


class ComplianceTracker:
    """Compliance and data retention management"""

    def __init__(self):
        """Initialize compliance tracker"""
        self.storage_path = Path(governance_config.compliance.retention_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.policies_file = self.storage_path / "retention_policies.json"
        self.rtbf_file = self.storage_path / "rtbf_requests.json"
        self.reports_file = self.storage_path / "compliance_reports.json"
        self.deletion_audit_file = self.storage_path / "deletion_audit.json"
        
        self.policies: Dict[str, RetentionPolicy] = self._load_policies()
        self.rtbf_requests: Dict[str, RTBFRequest] = self._load_rtbf_requests()
        self.reports: Dict[str, ComplianceReport] = self._load_reports()
        self.deletion_audits: List[DeletionAudit] = self._load_deletion_audits()
        
        self._initialize_default_policies()

    def create_retention_policy(self, asset_id: str, framework: str,
                               retention_days: int, purge_after_days: int,
                               description: str = "") -> str:
        """Create a retention policy for an asset"""
        from uuid import uuid4
        policy_id = str(uuid4())
        
        policy = RetentionPolicy(
            policy_id=policy_id,
            asset_id=asset_id,
            framework=framework,
            retention_days=retention_days,
            purge_after_days=purge_after_days,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            description=description
        )
        
        self.policies[policy_id] = policy
        self._save_policies()
        
        return policy_id

    def get_retention_policy(self, asset_id: str) -> Optional[RetentionPolicy]:
        """Get retention policy for an asset"""
        for policy in self.policies.values():
            if policy.asset_id == asset_id and policy.is_active:
                return policy
        return None

    def apply_retention_policy(self, asset_id: str) -> Dict:
        """Apply retention to an asset"""
        policy = self.get_retention_policy(asset_id)
        if not policy:
            return {"success": False, "message": "No retention policy found"}
        
        # Check if purge should happen
        retention_cutoff = datetime.now() - timedelta(days=policy.purge_after_days)
        
        return {
            "success": True,
            "asset_id": asset_id,
            "policy_id": policy.policy_id,
            "purge_threshold": retention_cutoff.isoformat(),
            "framework": policy.framework,
            "message": f"Retention policy applied: data older than {retention_cutoff.date()} will be purged"
        }

    def submit_rtbf_request(self, data_subject_id: str, asset_ids: List[str],
                           requested_by: str = "", reason: str = "") -> str:
        """Submit a right-to-be-forgotten request"""
        from uuid import uuid4
        request_id = str(uuid4())
        
        rtbf_request = RTBFRequest(
            request_id=request_id,
            data_subject_id=data_subject_id,
            asset_ids=asset_ids,
            requested_at=datetime.now().isoformat(),
            status="pending",
            reason=reason,
            requested_by=requested_by,
            assets_processed=[]
        )
        
        self.rtbf_requests[request_id] = rtbf_request
        self._save_rtbf_requests()
        
        return request_id

    def process_rtbf_request(self, request_id: str) -> Dict:
        """Process a right-to-be-forgotten request"""
        if request_id not in self.rtbf_requests:
            return {"success": False, "message": "RTBF request not found"}
        
        rtbf_request = self.rtbf_requests[request_id]
        rtbf_request.status = "processing"
        
        assets_processed = []
        
        for asset_id in rtbf_request.asset_ids:
            # In real implementation, would delete from actual data store
            # For now, simulate deletion tracking
            deletion_id = self._record_deletion(
                asset_id=asset_id,
                deletion_reason=f"RTBF request {request_id}",
                deleted_by=rtbf_request.requested_by,
                rtbf_request_id=request_id,
                records_deleted=0  # Would count actual deletions
            )
            assets_processed.append(asset_id)
        
        rtbf_request.status = "completed"
        rtbf_request.completed_at = datetime.now().isoformat()
        rtbf_request.assets_processed = assets_processed
        
        self._save_rtbf_requests()
        
        return {
            "success": True,
            "request_id": request_id,
            "data_subject_id": rtbf_request.data_subject_id,
            "assets_processed": len(assets_processed),
            "status": "completed"
        }

    def get_rtbf_status(self, request_id: str) -> Optional[RTBFRequest]:
        """Get status of an RTBF request"""
        return self.rtbf_requests.get(request_id)

    def assess_compliance(self, framework: str, scan_assets: List[Dict]) -> ComplianceReport:
        """Assess compliance with a framework"""
        from uuid import uuid4
        report_id = str(uuid4())
        
        compliant = 0
        issues = []
        recommendations = []
        assets_needing_attention = []
        
        # Framework-specific checks
        if framework == "gdpr":
            compliant, issues, recommendations = self._check_gdpr_compliance(scan_assets)
        elif framework == "ccpa":
            compliant, issues, recommendations = self._check_ccpa_compliance(scan_assets)
        elif framework == "hipaa":
            compliant, issues, recommendations = self._check_hipaa_compliance(scan_assets)
        elif framework == "soc2":
            compliant, issues, recommendations = self._check_soc2_compliance(scan_assets)
        
        # Identify assets with issues
        for issue in issues:
            if issue.get("asset_id") not in assets_needing_attention:
                assets_needing_attention.append(issue.get("asset_id"))
        
        overall_status = "compliant" if compliant == len(scan_assets) else (
            "partial" if compliant > 0 else "non_compliant"
        )
        
        report = ComplianceReport(
            report_id=report_id,
            framework=framework,
            generated_at=datetime.now().isoformat(),
            overall_status=overall_status,
            total_assets=len(scan_assets),
            scanned_assets=len(scan_assets),
            compliant_assets=compliant,
            issues=issues,
            recommendations=recommendations,
            assets_needing_attention=assets_needing_attention
        )
        
        self.reports[report_id] = report
        self._save_reports()
        
        return report

    def get_compliance_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Get a compliance report"""
        return self.reports.get(report_id)

    def get_deletion_audit_trail(self, asset_id: str = None, days: int = 90) -> List[DeletionAudit]:
        """Get deletion audit trail"""
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered = []
        
        for audit in self.deletion_audits:
            delete_time = datetime.fromisoformat(audit.deleted_at)
            if delete_time < cutoff_date:
                continue
            
            if asset_id and audit.asset_id != asset_id:
                continue
            
            filtered.append(audit)
        
        return filtered

    def generate_compliance_summary(self, frameworks: List[str] = None) -> Dict:
        """Generate overall compliance summary"""
        if frameworks is None:
            frameworks = [f.value for f in ComplianceFramework]
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "frameworks": {},
            "overall_status": "compliant"
        }
        
        for framework in frameworks:
            # Get latest report for framework
            framework_reports = [r for r in self.reports.values()
                               if r.framework == framework]
            
            if framework_reports:
                latest = max(framework_reports, key=lambda r: r.generated_at)
                summary["frameworks"][framework] = {
                    "status": latest.overall_status,
                    "scanned_assets": latest.scanned_assets,
                    "compliant_assets": latest.compliant_assets,
                    "issues_count": len(latest.issues) if latest.issues else 0,
                    "last_assessment": latest.generated_at
                }
                
                if latest.overall_status != "compliant":
                    summary["overall_status"] = "non_compliant"
            else:
                summary["frameworks"][framework] = {
                    "status": "not_assessed",
                    "last_assessment": None
                }
        
        return summary

    def export_compliance_data(self, export_path: str, frameworks: List[str] = None) -> bool:
        """Export compliance data for audit"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "retention_policies": [asdict(p) for p in self.policies.values()],
                "rtbf_requests": [asdict(r) for r in self.rtbf_requests.values()],
                "compliance_reports": [asdict(r) for r in self.reports.values()],
                "deletion_audits": [asdict(d) for d in self.deletion_audits]
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting compliance data: {e}")
            return False

    def _check_gdpr_compliance(self, assets: List[Dict]) -> tuple:
        """Check GDPR compliance"""
        compliant = 0
        issues = []
        recommendations = []
        
        for asset in assets:
            asset_issues = []
            
            # Check 1: PII handling
            if asset.get("contains_pii") and not asset.get("encryption_enabled"):
                asset_issues.append({
                    "asset_id": asset.get("id"),
                    "issue": "PII data not encrypted",
                    "severity": "high"
                })
            
            # Check 2: Retention policy
            if asset.get("contains_pii") and not self.get_retention_policy(asset.get("id")):
                asset_issues.append({
                    "asset_id": asset.get("id"),
                    "issue": "No retention policy for PII data",
                    "severity": "high"
                })
            
            # Check 3: Data ownership
            if not asset.get("owner"):
                asset_issues.append({
                    "asset_id": asset.get("id"),
                    "issue": "No data owner assigned",
                    "severity": "medium"
                })
            
            if not asset_issues:
                compliant += 1
            else:
                issues.extend(asset_issues)
        
        if not recommendations:
            recommendations = [
                "Implement encryption for all PII data",
                "Define and enforce retention policies",
                "Assign data owners to all assets",
                "Implement audit logging for data access",
                "Regular privacy impact assessments"
            ]
        
        return compliant, issues, recommendations

    def _check_ccpa_compliance(self, assets: List[Dict]) -> tuple:
        """Check CCPA compliance"""
        compliant = 0
        issues = []
        recommendations = []
        
        for asset in assets:
            asset_issues = []
            
            # Check 1: California resident data
            if asset.get("classification") == "RESTRICTED":
                if not asset.get("privacy_notice"):
                    asset_issues.append({
                        "asset_id": asset.get("id"),
                        "issue": "No privacy notice for personal data",
                        "severity": "high"
                    })
            
            # Check 2: Opt-out capability
            if asset.get("contains_pii"):
                if not asset.get("supports_opt_out"):
                    asset_issues.append({
                        "asset_id": asset.get("id"),
                        "issue": "No opt-out mechanism for personal data",
                        "severity": "high"
                    })
            
            if not asset_issues:
                compliant += 1
            else:
                issues.extend(asset_issues)
        
        recommendations = [
            "Implement privacy notices for all personal data",
            "Enable data subject rights (access, deletion, portability)",
            "Maintain opt-out mechanisms",
            "Regular vulnerability assessments",
            "Staff data privacy training"
        ]
        
        return compliant, issues, recommendations

    def _check_hipaa_compliance(self, assets: List[Dict]) -> tuple:
        """Check HIPAA compliance"""
        compliant = 0
        issues = []
        recommendations = []
        
        for asset in assets:
            asset_issues = []
            
            if asset.get("contains_pii"):  # Protected Health Information
                if not asset.get("encryption_enabled"):
                    asset_issues.append({
                        "asset_id": asset.get("id"),
                        "issue": "PHI not encrypted at rest",
                        "severity": "critical"
                    })
                
                if not asset.get("access_logging"):
                    asset_issues.append({
                        "asset_id": asset.get("id"),
                        "issue": "No access logging for PHI",
                        "severity": "high"
                    })
            
            if not asset_issues:
                compliant += 1
            else:
                issues.extend(asset_issues)
        
        recommendations = [
            "Implement encryption for all PHI (AES-256)",
            "Enable comprehensive access logging",
            "Implement access controls (RBAC)",
            "Business Associate Agreements (BAA)",
            "Regular security audits and risk assessments"
        ]
        
        return compliant, issues, recommendations

    def _check_soc2_compliance(self, assets: List[Dict]) -> tuple:
        """Check SOC2 compliance"""
        compliant = 0
        issues = []
        recommendations = []
        
        for asset in assets:
            asset_issues = []
            
            # Check 1: Availability
            if not asset.get("backup_enabled"):
                asset_issues.append({
                    "asset_id": asset.get("id"),
                    "issue": "Backups not enabled",
                    "severity": "high"
                })
            
            # Check 2: Confidentiality
            if asset.get("is_sensitive") and not asset.get("encryption_enabled"):
                asset_issues.append({
                    "asset_id": asset.get("id"),
                    "issue": "Sensitive data not encrypted",
                    "severity": "high"
                })
            
            # Check 3: Integrity
            if not asset.get("integrity_checks"):
                asset_issues.append({
                    "asset_id": asset.get("id"),
                    "issue": "No integrity checks enabled",
                    "severity": "medium"
                })
            
            if not asset_issues:
                compliant += 1
            else:
                issues.extend(asset_issues)
        
        recommendations = [
            "Enable backups for all critical assets",
            "Implement encryption (in-transit and at-rest)",
            "Enable integrity checks (checksums/hashing)",
            "Regular disaster recovery drills",
            "Incident response procedures"
        ]
        
        return compliant, issues, recommendations

    def _record_deletion(self, asset_id: str, deletion_reason: str,
                        deleted_by: str, rtbf_request_id: str = "",
                        records_deleted: int = 0) -> str:
        """Record a deletion event"""
        from uuid import uuid4
        deletion_id = str(uuid4())
        
        deletion_audit = DeletionAudit(
            deletion_id=deletion_id,
            asset_id=asset_id,
            deletion_reason=deletion_reason,
            deleted_at=datetime.now().isoformat(),
            deleted_by=deleted_by,
            records_deleted=records_deleted,
            rtbf_request_id=rtbf_request_id,
            verification={"checksum": "pending"}
        )
        
        self.deletion_audits.append(deletion_audit)
        self._save_deletion_audits()
        
        return deletion_id

    def _initialize_default_policies(self):
        """Initialize default retention policies"""
        if self.policies_file.exists():
            return  # Already initialized
        
        default_policies = {
            "bronze_default": {
                "asset_id": "bronze_layer",
                "framework": "gdpr",
                "retention_days": 365,
                "purge_after_days": 730,
                "description": "Default policy for bronze layer raw data"
            },
            "silver_default": {
                "asset_id": "silver_layer",
                "framework": "gdpr",
                "retention_days": 730,
                "purge_after_days": 1095,
                "description": "Default policy for silver layer processed data"
            },
            "gold_default": {
                "asset_id": "gold_layer",
                "framework": "gdpr",
                "retention_days": 1825,
                "purge_after_days": 2555,
                "description": "Default policy for gold layer aggregated data"
            }
        }

    def _load_policies(self) -> Dict[str, RetentionPolicy]:
        """Load retention policies"""
        if not self.policies_file.exists():
            return {}
        
        try:
            with open(self.policies_file, 'r') as f:
                data = json.load(f)
                return {pid: RetentionPolicy(**pdata) for pid, pdata in data.items()}
        except Exception as e:
            print(f"Error loading policies: {e}")
            return {}

    def _load_rtbf_requests(self) -> Dict[str, RTBFRequest]:
        """Load RTBF requests"""
        if not self.rtbf_file.exists():
            return {}
        
        try:
            with open(self.rtbf_file, 'r') as f:
                data = json.load(f)
                return {rid: RTBFRequest(**rdata) for rid, rdata in data.items()}
        except Exception as e:
            print(f"Error loading RTBF requests: {e}")
            return {}

    def _load_reports(self) -> Dict[str, ComplianceReport]:
        """Load compliance reports"""
        if not self.reports_file.exists():
            return {}
        
        try:
            with open(self.reports_file, 'r') as f:
                data = json.load(f)
                return {rid: ComplianceReport(**rdata) for rid, rdata in data.items()}
        except Exception as e:
            print(f"Error loading reports: {e}")
            return {}

    def _load_deletion_audits(self) -> List[DeletionAudit]:
        """Load deletion audit trails"""
        if not self.deletion_audit_file.exists():
            return []
        
        try:
            with open(self.deletion_audit_file, 'r') as f:
                data = json.load(f)
                return [DeletionAudit(**audit) for audit in data]
        except Exception as e:
            print(f"Error loading deletion audits: {e}")
            return []

    def _save_policies(self):
        """Save retention policies"""
        try:
            data = {pid: asdict(p) for pid, p in self.policies.items()}
            with open(self.policies_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving policies: {e}")

    def _save_rtbf_requests(self):
        """Save RTBF requests"""
        try:
            data = {rid: asdict(r) for rid, r in self.rtbf_requests.items()}
            with open(self.rtbf_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving RTBF requests: {e}")

    def _save_reports(self):
        """Save compliance reports"""
        try:
            data = {rid: asdict(r) for rid, r in self.reports.items()}
            with open(self.reports_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving reports: {e}")

    def _save_deletion_audits(self):
        """Save deletion audit trails"""
        try:
            with open(self.deletion_audit_file, 'w') as f:
                json.dump([asdict(d) for d in self.deletion_audits], f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving deletion audits: {e}")


# Global compliance tracker instance
_compliance_tracker = None

def get_compliance_tracker() -> ComplianceTracker:
    """Get or create global compliance tracker"""
    global _compliance_tracker
    if _compliance_tracker is None:
        _compliance_tracker = ComplianceTracker()
    return _compliance_tracker
