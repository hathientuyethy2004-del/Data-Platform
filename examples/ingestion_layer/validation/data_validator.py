"""
Data Validation Module - Ingestion Layer
Kiểm tra chất lượng dữ liệu từ các Kafka topics
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Kết quả validation cho một tin nhắn"""
    is_valid: bool
    topic: str
    errors: List[str]
    warnings: List[str]
    checks_passed: int
    checks_total: int
    timestamp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), default=str)


class DataValidator:
    """
    Validator cho dữ liệu từ Kafka
    - Kiểm tra required fields
    - Kiểm tra data types
    - Kiểm tra business rules
    - Kiểm tra statistics
    """

    # Validation rules cho từng topic
    VALIDATION_SCHEMAS = {
        "topic_app_events": {
            "required_fields": {
                "event_type": str,
                "user_id": str,
                "session_id": str,
                "timestamp": str,
                "app_type": str
            },
            "optional_fields": {
                "properties": dict,
                "source": str,
                "version": str
            },
            "constraints": {
                "event_type": ["page_view", "click", "purchase", "scroll", "search"],
                "app_type": ["mobile", "web", "api"],
                "user_id_len_min": 1,
                "user_id_len_max": 255
            }
        },
        
        "topic_cdc_changes": {
            "required_fields": {
                "op": str,  # i=insert, u=update, d=delete
                "table": str,
                "before": (dict, type(None)),
                "after": (dict, type(None)),
                "ts_ms": int
            },
            "optional_fields": {
                "db": str,
                "schema": str,
                "txId": int,
                "lsn": int
            },
            "constraints": {
                "op": ["i", "u", "d"],
                "table": ["users", "bookings", "payments"]
            }
        },
        
        "topic_clickstream": {
            "required_fields": {
                "event_id": str,
                "user_id": str,
                "page_url": str,
                "timestamp": str,
                "event_type": str
            },
            "optional_fields": {
                "element_id": str,
                "x_pos": (int, float),
                "y_pos": (int, float),
                "device_type": str,
                "session_id": str
            },
            "constraints": {
                "event_type": ["click", "scroll", "hover", "focus"],
                "device_type": ["desktop", "mobile", "tablet"]
            }
        },
        
        "topic_external_data": {
            "required_fields": {
                "data_source": str,
                "timestamp": str
            },
            "optional_fields": {
                "data": dict,
                "location": str,
                "value": (int, float, str),
                "status": str
            },
            "constraints": {
                "data_source": ["weather", "maps", "social_media", "market_data", "news"]
            }
        }
    }

    def __init__(self):
        self.validation_stats = {
            "total_validated": 0,
            "passed": 0,
            "failed": 0,
            "by_topic": {}
        }

    def validate_message(self, message: Dict, topic: str) -> ValidationResult:
        """
        Validate một tin nhắn
        
        Args:
            message: Tin nhắn từ Kafka
            topic: Topic của tin nhắn
            
        Returns:
            ValidationResult object
        """
        errors = []
        warnings = []
        checks_passed = 0
        checks_total = 0

        schema = self.VALIDATION_SCHEMAS.get(topic, {})
        if not schema:
            warnings.append(f"No validation schema defined for topic: {topic}")
            return ValidationResult(
                is_valid=True,
                topic=topic,
                errors=errors,
                warnings=warnings,
                checks_passed=checks_passed,
                checks_total=checks_total,
                timestamp=datetime.utcnow().isoformat()
            )

        # Check required fields
        required_fields = schema.get("required_fields", {})
        for field_name, field_type in required_fields.items():
            checks_total += 1
            if field_name not in message:
                errors.append(f"Missing required field: {field_name}")
            else:
                # Type check
                value = message[field_name]
                if not isinstance(value, field_type):
                    errors.append(
                        f"Field '{field_name}' has wrong type. "
                        f"Expected {field_type}, got {type(value).__name__}"
                    )
                else:
                    checks_passed += 1

        # Check optional fields (type only if present)
        optional_fields = schema.get("optional_fields", {})
        for field_name, field_type in optional_fields.items():
            if field_name in message:
                checks_total += 1
                value = message[field_name]
                if not isinstance(value, field_type):
                    warnings.append(
                        f"Field '{field_name}' has wrong type. "
                        f"Expected {field_type}, got {type(value).__name__}"
                    )
                else:
                    checks_passed += 1

        # Check constraints
        constraints = schema.get("constraints", {})
        for field_name, allowed_values in constraints.items():
            if field_name in message and isinstance(allowed_values, list):
                checks_total += 1
                value = message[field_name]
                if value not in allowed_values:
                    errors.append(
                        f"Field '{field_name}' value '{value}' not in allowed values: {allowed_values}"
                    )
                else:
                    checks_passed += 1

        # Validate specific formats
        if "timestamp" in message and isinstance(message["timestamp"], str):
            checks_total += 1
            try:
                datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
                checks_passed += 1
            except ValueError:
                errors.append(f"Invalid timestamp format: {message['timestamp']}")

        # Update statistics
        self.validation_stats["total_validated"] += 1
        is_valid = len(errors) == 0
        if is_valid:
            self.validation_stats["passed"] += 1
        else:
            self.validation_stats["failed"] += 1

        if topic not in self.validation_stats["by_topic"]:
            self.validation_stats["by_topic"][topic] = {"passed": 0, "failed": 0}
        
        if is_valid:
            self.validation_stats["by_topic"][topic]["passed"] += 1
        else:
            self.validation_stats["by_topic"][topic]["failed"] += 1

        return ValidationResult(
            is_valid=is_valid,
            topic=topic,
            errors=errors,
            warnings=warnings,
            checks_passed=checks_passed,
            checks_total=checks_total,
            timestamp=datetime.utcnow().isoformat()
        )

    def validate_batch(self, messages: List[Dict], topic: str) -> Dict[str, Any]:
        """
        Validate một batch tin nhắn
        
        Args:
            messages: Danh sách tin nhắn
            topic: Topic
            
        Returns:
            Dict với kết quả validation
        """
        results = {
            "total": len(messages),
            "valid": 0,
            "invalid": 0,
            "errors": [],
            "warnings": []
        }

        for msg in messages:
            result = self.validate_message(msg, topic)
            if result.is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["errors"].extend(result.errors)
            results["warnings"].extend(result.warnings)

        return results

    def get_validation_stats(self) -> Dict:
        """Lấy thống kê validation"""
        return self.validation_stats.copy()

    def print_validation_stats(self):
        """In ra thống kê validation"""
        stats = self.get_validation_stats()
        total = stats["total_validated"]
        passed = stats["passed"]
        failed = stats["failed"]
        
        if total > 0:
            pass_rate = (passed / total) * 100
            logger.info(
                f"\n✅ Validation Statistics:\n"
                f"  Total validated: {total}\n"
                f"  Passed: {passed} ({pass_rate:.1f}%)\n"
                f"  Failed: {failed}\n"
                f"  By topic:\n"
            )
            for topic, counts in stats["by_topic"].items():
                topic_total = counts["passed"] + counts["failed"]
                if topic_total > 0:
                    topic_pass_rate = (counts["passed"] / topic_total) * 100
                    logger.info(
                        f"    {topic}: {counts['passed']}/{topic_total} "
                        f"({topic_pass_rate:.1f}%)"
                    )


class ValidationRuleBuilder:
    """Builder pattern để tạo validation rules custom"""

    def __init__(self, topic: str):
        self.topic = topic
        self.schema = {
            "required_fields": {},
            "optional_fields": {},
            "constraints": {}
        }

    def add_required_field(self, field_name: str, field_type) -> "ValidationRuleBuilder":
        """Thêm required field"""
        self.schema["required_fields"][field_name] = field_type
        return self

    def add_optional_field(self, field_name: str, field_type) -> "ValidationRuleBuilder":
        """Thêm optional field"""
        self.schema["optional_fields"][field_name] = field_type
        return self

    def add_constraint(self, field_name: str, allowed_values: List) -> "ValidationRuleBuilder":
        """Thêm constraint"""
        self.schema["constraints"][field_name] = allowed_values
        return self

    def build(self) -> Dict:
        """Build schema"""
        return self.schema


if __name__ == "__main__":
    # Test validation
    validator = DataValidator()

    # Test message
    test_messages = [
        {
            "event_type": "page_view",
            "user_id": "user123",
            "session_id": "sess456",
            "timestamp": "2026-02-16T12:00:00Z",
            "app_type": "web"
        },
        {
            "event_type": "invalid_type",
            "user_id": "user456",
            "session_id": "sess789",
            "timestamp": "invalid-timestamp",
            "app_type": "web"
        }
    ]

    for msg in test_messages:
        result = validator.validate_message(msg, "topic_app_events")
        print(f"Topic: {result.topic}")
        print(f"Valid: {result.is_valid}")
        print(f"Errors: {result.errors}")
        print(f"Checks: {result.checks_passed}/{result.checks_total}\n")

    validator.print_validation_stats()
