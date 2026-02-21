"""
Tests for Compliance Auditing Product

Test coverage:
- Audit trail collection and integrity
- GDPR compliance checks
- Data retention validation
- Compliance violation detection
- Data subject request processing
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from src.ingestion.audit_collector import (
    AuditTrailCollector, DataAccessEvent, DataDeletionEvent,
    APIAuditEvent, ComplianceChecker
)
from src.processing.compliance_engine import (
    GDPRComplianceEngine, DataRetentionManager,
    AccessControlValidator, ComplianceReportGenerator
)
from src.monitoring.health_checks import (
    ComplianceHealthMonitor, AuditTrailValidator,
    ComplianceMetricsCollector
)


class TestAuditTrailCollector:
    """Tests for audit trail collection"""
    
    @pytest.fixture
    def collector(self):
        return AuditTrailCollector()
    
    def test_record_data_access(self, collector):
        """Test recording data access event"""
        event = DataAccessEvent(
            event_id="evt_001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id="user_123",
            dataset="customer_data",
            columns_accessed=["email", "name"],
            rows_accessed=1000,
            query_hash="hash_123",
            pii_fields_accessed=["email"],
            purpose="customer_analysis",
        )
        
        event_id = collector.record_data_access(event)
        
        assert event_id == "evt_001"
        assert len(collector.event_buffer) == 1
    
    def test_record_data_deletion(self, collector):
        """Test recording data deletion event"""
        event = DataDeletionEvent(
            event_id="evt_002",
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id="req_123",
            subject_id="subj_456",
            deletion_reason="gdpr_rtbf",
            datasets_affected=["user_profiles"],
            records_deleted=10000,
            status="completed",
        )
        
        event_id = collector.record_data_deletion(event)
        
        assert event_id == "evt_002"
    
    def test_record_api_call(self, collector):
        """Test recording API call event"""
        event = APIAuditEvent(
            event_id="evt_003",
            timestamp=datetime.now(timezone.utc).isoformat(),
            api_path="/api/v1/users",
            method="GET",
            user_id="user_123",
            response_status=200,
            response_time_ms=150,
            request_data_size_bytes=0,
            response_data_size_bytes=5000,
            pii_in_request=False,
            pii_in_response=True,
        )
        
        event_id = collector.record_api_call(event)
        
        assert event_id == "evt_003"
    
    def test_retention_policy(self, collector):
        """Test retention policy lookup"""
        retention = collector.get_retention_policy("pii")
        
        assert retention == 730  # 2 years


class TestGDPRComplianceEngine:
    """Tests for GDPR compliance"""
    
    @pytest.fixture
    def engine(self):
        return GDPRComplianceEngine()
    
    def test_retention_compliance_check_compliant(self, engine):
        """Test retention compliance - compliant"""
        result = engine.check_data_retention_compliance(
            "dataset_1",
            current_age_days=100,
            classification="pii",
            last_access_date=datetime.now(timezone.utc).isoformat()
        )
        
        assert result["compliant"] is True
    
    def test_retention_compliance_check_non_compliant(self, engine):
        """Test retention compliance - non-compliant"""
        result = engine.check_data_retention_compliance(
            "dataset_2",
            current_age_days=400,
            classification="customer_data",
            last_access_date=(datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
        )
        
        assert result["compliant"] is False
        assert "violation" in result
    
    def test_right_to_be_forgotten(self, engine):
        """Test GDPR right to be forgotten request"""
        result = engine.check_right_to_be_forgotten(
            "subject_123",
            ["data_1", "data_2"],
            "user_request"
        )
        
        assert "request_id" in result
        assert result["status"] == "pending"
        assert len(result["datasets_to_process"]) == 2
    
    def test_purpose_limitation(self, engine):
        """Test purpose limitation check"""
        result = engine.check_purpose_limitation(
            "customer_data",
            "analytics",
            ["analytics", "operations"]
        )
        
        assert result["compliant"] is True
    
    def test_data_minimization(self, engine):
        """Test data minimization check"""
        result = engine.check_data_minimization(
            "user_data",
            ["email", "name", "phone", "address"],
            ["email", "name"]
        )
        
        assert result["compliant"] is False
        assert len(result["unnecessary_fields"]) == 2


class TestDataRetentionManager:
    """Tests for data retention management"""
    
    @pytest.fixture
    def manager(self):
        return DataRetentionManager()
    
    def test_schedule_deletion(self, manager):
        """Test scheduling deletion"""
        result = manager.schedule_deletion(
            "old_dataset",
            "retention_exceeded",
            (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        )
        
        assert result["status"] == "scheduled"
        assert result["dataset"] == "old_dataset"
    
    def test_get_retention_policy(self, manager):
        """Test getting retention policy"""
        policy = manager.get_retention_policy("transactional")
        
        assert policy["retention_days"] == 90


class TestAccessControlValidator:
    """Tests for access control"""
    
    @pytest.fixture
    def validator(self):
        return AccessControlValidator()
    
    def test_admin_access_all_data(self, validator):
        """Test admin can access all classifications"""
        allowed, reason = validator.validate_access(
            "admin_1",
            "sensitive_data",
            "pii",
            "admin"
        )
        
        assert allowed is True
    
    def test_viewer_restricted_access(self, validator):
        """Test viewer can only access public"""
        allowed, reason = validator.validate_access(
            "viewer_1",
            "restricted_data",
            "confidential",
            "viewer"
        )
        
        assert allowed is False


class TestComplianceHealthMonitor:
    """Tests for compliance monitoring"""
    
    @pytest.fixture
    def monitor(self):
        return ComplianceHealthMonitor()
    
    def test_audit_trail_integrity_check(self, monitor):
        """Test audit trail integrity check"""
        check = monitor.check_audit_trail_integrity()
        
        assert check["status"] == "HEALTHY"
        assert check["metrics"]["integrity_rate"] > 99.0
    
    def test_gdpr_compliance_check(self, monitor):
        """Test GDPR compliance check"""
        check = monitor.check_gdpr_compliance()
        
        assert check["check_name"] == "gdpr_compliance"
        assert "metrics" in check
    
    def test_retention_schedule_check(self, monitor):
        """Test retention schedule check"""
        check = monitor.check_data_retention_schedule()
        
        assert check["check_name"] == "retention_schedule"
    
    def test_pii_access_patterns_check(self, monitor):
        """Test PII access patterns check"""
        check = monitor.check_pii_access_patterns()
        
        assert check["check_name"] == "pii_access_patterns"
    
    def test_run_all_health_checks(self, monitor):
        """Test running all health checks"""
        result = monitor.run_all_health_checks()
        
        assert "overall_status" in result
        assert len(result["checks"]) == 5


class TestAuditTrailValidator:
    """Tests for audit trail validation"""
    
    @pytest.fixture
    def validator(self):
        return AuditTrailValidator()
    
    def test_validate_immutability(self, validator):
        """Test audit trail immutability validation"""
        records = [
            {"event_id": "evt_1", "timestamp": "2024-02-18T12:00:00Z"},
            {"event_id": "evt_2", "timestamp": "2024-02-18T12:01:00Z"},
        ]
        
        result = validator.validate_immutability(records)
        
        assert result["integrity_verified"] is True
        assert result["records_invalid"] == 0
    
    def test_validate_completeness(self, validator):
        """Test audit trail completeness validation"""
        result = validator.validate_completeness(
            "2024-02-18T00:00:00Z",
            "2024-02-18T23:59:59Z"
        )
        
        assert result["gaps_detected"] == 0


class TestComplianceMetricsCollector:
    """Tests for compliance metrics collection"""
    
    @pytest.fixture
    def collector(self):
        return ComplianceMetricsCollector()
    
    def test_collect_violation_metrics(self, collector):
        """Test collecting violation metrics"""
        metrics = collector.collect_violation_metrics()
        
        assert "total_violations" in metrics
        assert "by_severity" in metrics
    
    def test_get_compliance_dashboard(self, collector):
        """Test getting compliance dashboard"""
        dashboard = collector.get_compliance_dashboard()
        
        assert "overall_compliance_score" in dashboard
        assert "violations" in dashboard
        assert "retention" in dashboard


class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_compliance_workflow(self):
        """Test end-to-end compliance workflow"""
        # Collect audit
        collector = AuditTrailCollector()
        
        event = DataAccessEvent(
            event_id="evt_001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id="user_123",
            dataset="customer_data",
            columns_accessed=["email"],
            rows_accessed=100,
            query_hash="hash",
            pii_fields_accessed=["email"],
            purpose="analysis",
        )
        
        collector.record_data_access(event)
        
        # Check compliance
        checker = ComplianceChecker()
        result = checker.check_pii_access_logging(event)
        
        assert "event_id" in result
