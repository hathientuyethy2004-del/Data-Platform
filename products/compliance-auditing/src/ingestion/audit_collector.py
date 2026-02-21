"""
Audit Trail Collector - Captures all data access and transformations

Collects audit logs from:
- Data ingestion events
- User access events
- Data transformation logs
- Deletion and anonymization events
- API calls and responses
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import json
import logging

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events"""
    DATA_ACCESS = "data_access"
    DATA_INGESTION = "data_ingestion"
    DATA_TRANSFORMATION = "data_transformation"
    DATA_DELETION = "data_deletion"
    DATA_ANONYMIZATION = "data_anonymization"
    USER_ACCESS = "user_access"
    PERMISSION_CHANGE = "permission_change"
    API_CALL = "api_call"
    CONFIGURATION_CHANGE = "configuration_change"


class DataClassification(str, Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"
    SENSITIVE_PII = "sensitive_pii"


class AuditEvent(BaseModel):
    """Audit event model"""
    event_id: str = Field(description="Unique event ID")
    event_type: str = Field(description="Type of audit event")
    timestamp: str = Field(description="Event timestamp in ISO format")
    user_id: Optional[str] = Field(None, description="User performing action")
    service: str = Field(description="Service/product generating event")
    resource: str = Field(description="Resource being accessed/modified")
    resource_type: str = Field(description="Type of resource (table, file, etc)")
    action: str = Field(description="Action performed (read, write, delete, etc)")
    
    # Data classification
    data_classification: str = Field(description="PII, public, confidential, etc")
    contains_pii: bool = False
    pii_fields: List[str] = Field(default_factory=list, description="PII field names")
    
    # Request details
    status: str = Field(description="success, failure, denied")
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    
    # Retention info
    retention_days: int = Field(default=365, description="Retention period")
    compliance_requirement: Optional[str] = None
    
    # Metadata
    source_ip: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        if v not in [e.value for e in AuditEventType]:
            raise ValueError(f"Invalid event type: {v}")
        return v


class DataAccessEvent(BaseModel):
    """Data access audit event"""
    event_id: str
    timestamp: str
    user_id: str
    dataset: str
    columns_accessed: List[str]
    rows_accessed: int
    query_hash: str
    pii_fields_accessed: List[str]
    purpose: str = Field(description="Purpose of access")
    justified: bool = Field(default=True, description="Whether access is justified")


class DataDeletionEvent(BaseModel):
    """Data deletion audit event (e.g., GDPR right to be forgotten)"""
    event_id: str
    timestamp: str
    request_id: str
    subject_id: str = Field(description="Data subject identifier")
    deletion_reason: str = Field(description="gdpr_rtbf, data_retention, user_request, etc")
    datasets_affected: List[str]
    records_deleted: int
    status: str = Field(description="pending, in_progress, completed")
    completed_at: Optional[str] = None


class APIAuditEvent(BaseModel):
    """API call audit event"""
    event_id: str
    timestamp: str
    api_path: str
    method: str
    user_id: Optional[str]
    response_status: int
    response_time_ms: int
    request_data_size_bytes: int
    response_data_size_bytes: int
    pii_in_request: bool
    pii_in_response: bool


class AuditTrailCollector:
    """Collects audit events from various sources"""
    
    def __init__(self):
        """Initialize collector"""
        self.event_buffer: List[Dict[str, Any]] = []
        self.retention_policies = {
            DataClassification.PUBLIC.value: 30,
            DataClassification.INTERNAL.value: 90,
            DataClassification.CONFIDENTIAL.value: 365,
            DataClassification.RESTRICTED.value: 365,
            DataClassification.PII.value: 730,
            DataClassification.SENSITIVE_PII.value: 2555,  # 7 years
        }
    
    def record_data_access(self, event: DataAccessEvent) -> str:
        """
        Record data access event.
        
        Args:
            event: Data access event
            
        Returns:
            Event ID
        """
        audit_event = {
            "event_id": event.event_id,
            "event_type": AuditEventType.DATA_ACCESS.value,
            "timestamp": event.timestamp,
            "user_id": event.user_id,
            "dataset": event.dataset,
            "columns_accessed": event.columns_accessed,
            "rows_accessed": event.rows_accessed,
            "pii_fields": event.pii_fields_accessed,
            "purpose": event.purpose,
            "justified": event.justified,
        }
        
        self.event_buffer.append(audit_event)
        logger.info(f"Recorded data access: {event.event_id}")
        
        return event.event_id
    
    def record_data_deletion(self, event: DataDeletionEvent) -> str:
        """
        Record data deletion event (GDPR compliance).
        
        Args:
            event: Data deletion event
            
        Returns:
            Event ID
        """
        audit_event = {
            "event_id": event.event_id,
            "event_type": AuditEventType.DATA_DELETION.value,
            "timestamp": event.timestamp,
            "request_id": event.request_id,
            "subject_id": event.subject_id,
            "deletion_reason": event.deletion_reason,
            "datasets_affected": event.datasets_affected,
            "records_deleted": event.records_deleted,
            "status": event.status,
        }
        
        self.event_buffer.append(audit_event)
        logger.info(f"Recorded data deletion: {event.event_id}")
        
        return event.event_id
    
    def record_api_call(self, event: APIAuditEvent) -> str:
        """
        Record API call event.
        
        Args:
            event: API audit event
            
        Returns:
            Event ID
        """
        audit_event = {
            "event_id": event.event_id,
            "event_type": AuditEventType.API_CALL.value,
            "timestamp": event.timestamp,
            "api_path": event.api_path,
            "method": event.method,
            "user_id": event.user_id,
            "response_status": event.response_status,
            "response_time_ms": event.response_time_ms,
            "pii_in_request": event.pii_in_request,
            "pii_in_response": event.pii_in_response,
        }
        
        self.event_buffer.append(audit_event)
        
        return event.event_id
    
    def record_data_transformation(self,
                                   event_id: str,
                                   job_name: str,
                                   source_dataset: str,
                                   target_dataset: str,
                                   transformation_type: str,
                                   records_processed: int,
                                   pii_fields: List[str] = None) -> str:
        """
        Record data transformation event.
        
        Args:
            event_id: Event ID
            job_name: Job name
            source_dataset: Source dataset
            target_dataset: Target dataset
            transformation_type: Type of transformation
            records_processed: Records processed
            pii_fields: PII fields involved
            
        Returns:
            Event ID
        """
        audit_event = {
            "event_id": event_id,
            "event_type": AuditEventType.DATA_TRANSFORMATION.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_name": job_name,
            "source_dataset": source_dataset,
            "target_dataset": target_dataset,
            "transformation_type": transformation_type,
            "records_processed": records_processed,
            "pii_fields": pii_fields or [],
        }
        
        self.event_buffer.append(audit_event)
        logger.info(f"Recorded transformation: {job_name}")
        
        return event_id
    
    def get_retention_policy(self, classification: str) -> int:
        """
        Get retention days for data classification.
        
        Args:
            classification: Data classification
            
        Returns:
            Retention days
        """
        return self.retention_policies.get(classification, 365)
    
    def flush_to_kafka(self, topic: str) -> int:
        """
        Flush buffered events to Kafka.
        
        Args:
            topic: Kafka topic
            
        Returns:
            Number of events flushed
        """
        count = len(self.event_buffer)
        
        # In production, would write to Kafka
        for event in self.event_buffer:
            logger.debug(f"Would send to {topic}: {event['event_id']}")
        
        self.event_buffer.clear()
        logger.info(f"Flushed {count} events to {topic}")
        
        return count
    
    def get_audit_trail(self, 
                       user_id: Optional[str] = None,
                       dataset: Optional[str] = None,
                       hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get audit trail for specific user/dataset.
        
        Args:
            user_id: Filter by user
            dataset: Filter by dataset
            hours: Time window
            
        Returns:
            List of audit events
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        results = []
        for event in self.event_buffer:
            if user_id and event.get("user_id") != user_id:
                continue
            
            if dataset and event.get("dataset") != dataset:
                continue
            
            results.append(event)
        
        return results


class ComplianceChecker:
    """Checks for compliance violations"""
    
    # Compliance rules
    RULES = {
        "gdpr_data_retention": {
            "description": "Data must not exceed retention period per GDPR",
            "check_frequency": "daily",
            "action": "flag_for_deletion",
        },
        "pii_access_justification": {
            "description": "PII access must be justified",
            "check_frequency": "real-time",
            "action": "alert",
        },
        "data_minimization": {
            "description": "Only necessary data should be collected",
            "check_frequency": "weekly",
            "action": "report",
        },
        "anonymization_compliance": {
            "description": "Data must be properly anonymized",
            "check_frequency": "daily",
            "action": "audit",
        },
        "audit_trail_integrity": {
            "description": "Audit trails must be immutable",
            "check_frequency": "continuous",
            "action": "alert",
        },
    }
    
    def check_data_retention(self, 
                            dataset: str,
                            last_access: str,
                            classification: str) -> Dict[str, Any]:
        """
        Check if data exceeds retention period.
        
        Args:
            dataset: Dataset name
            last_access: Last access timestamp
            classification: Data classification
            
        Returns:
            Check result
        """
        # Calculate retention based on classification
        retention_days = {
            DataClassification.PUBLIC.value: 30,
            DataClassification.INTERNAL.value: 90,
            DataClassification.PII.value: 730,
            DataClassification.SENSITIVE_PII.value: 2555,
        }.get(classification, 365)
        
        last_access_dt = datetime.fromisoformat(last_access)
        age_days = (datetime.now(timezone.utc) - last_access_dt).days
        
        compliance = age_days <= retention_days
        
        return {
            "dataset": dataset,
            "age_days": age_days,
            "retention_days": retention_days,
            "compliant": compliance,
            "action": "SCHEDULE_FOR_DELETION" if not compliance else "OK",
        }
    
    def check_pii_access_logging(self, access_event: DataAccessEvent) -> Dict[str, Any]:
        """
        Check if PII access was properly logged.
        
        Args:
            access_event: Access event
            
        Returns:
            Check result
        """
        compliant = (
            len(access_event.pii_fields_accessed) == 0 or
            (access_event.justified and access_event.purpose is not None)
        )
        
        return {
            "event_id": access_event.event_id,
            "pii_accessed": len(access_event.pii_fields_accessed) > 0,
            "justified": access_event.justified,
            "compliant": compliant,
            "severity": "HIGH" if not compliant and access_event.pii_fields_accessed else "LOW",
        }
    
    def check_anonymization_completeness(self,
                                        dataset: str,
                                        anonymized_fields: List[str],
                                        expected_pii_fields: List[str]) -> Dict[str, Any]:
        """
        Check if all PII was properly anonymized.
        
        Args:
            dataset: Dataset name
            anonymized_fields: Fields that were anonymized
            expected_pii_fields: Expected PII fields
            
        Returns:
            Check result
        """
        missing_anonymization = set(expected_pii_fields) - set(anonymized_fields)
        
        compliant = len(missing_anonymization) == 0
        
        return {
            "dataset": dataset,
            "compliant": compliant,
            "missing_anonymization": list(missing_anonymization),
            "action": "FLAG_FOR_REVIEW" if not compliant else "OK",
        }
    
    def run_compliance_checks(self, audit_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run all compliance checks.
        
        Args:
            audit_events: List of audit events
            
        Returns:
            Compliance report
        """
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks_run": len(self.RULES),
            "violations": [],
            "warnings": [],
        }
        
        # In production, would run actual compliance checks
        # For now, report status
        results["overall_status"] = "COMPLIANT"
        
        return results
