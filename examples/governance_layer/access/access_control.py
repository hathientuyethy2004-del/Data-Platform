"""
Access Control & Audit System
Role-based access control (RBAC), API key management, and audit logging
"""

import json
import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

from config.governance_config import governance_config


class UserRole(Enum):
    """User roles"""
    ADMIN = "admin"                    # Full system access
    DATA_OWNER = "data_owner"          # Own data assets
    DATA_STEWARD = "data_steward"      # Manage catalog/quality
    ANALYST = "analyst"                # Query and analyze
    DEVELOPER = "developer"            # Access APIs/SDKs
    VIEWER = "viewer"                  # Read-only access
    AUDITOR = "auditor"                # Access audit logs


class ResourceType(Enum):
    """Resource types for access control"""
    ASSET = "asset"
    CATALOG = "catalog"
    LINEAGE = "lineage"
    QUALITY = "quality"
    POLICY = "policy"
    API = "api"
    AUDIT = "audit"


class AccessAction(Enum):
    """Allowed actions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass
class APIKey:
    """API key for programmatic access"""
    key_id: str
    key_hash: str  # SHA-256 hash of actual key
    owner: str
    created_at: str
    expires_at: str
    is_active: bool = True
    last_used: Optional[str] = None
    name: str = ""
    scopes: List[str] = None  # List of allowed operations
    rate_limit: int = 1000  # Requests per hour
    ip_whitelist: List[str] = None  # IP addresses allowed

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ["read"]
        if self.ip_whitelist is None:
            self.ip_whitelist = []


@dataclass
class RolePermission:
    """Role-based permission"""
    role: str
    resource_type: str
    action: str
    asset_level: bool = False  # Can be controlled at asset level
    conditions: Dict = None  # Additional conditions


@dataclass
class AuditLog:
    """Audit log entry"""
    log_id: str
    timestamp: str
    user: str
    action: str
    resource_type: str
    resource_id: str
    status: str  # success, failure, denied
    changes: Dict = None
    ip_address: str = ""
    user_agent: str = ""
    error_message: str = ""


class AccessControlManager:
    """Access control and audit management"""

    def __init__(self):
        """Initialize access control manager"""
        self.storage_path = Path(governance_config.access.access_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.roles_file = self.storage_path / "roles.json"
        self.api_keys_file = self.storage_path / "api_keys.json"
        self.audit_logs_file = self.storage_path / "audit_logs.json"
        
        self.roles: Dict[str, Set[RolePermission]] = self._load_roles()
        self.api_keys: Dict[str, APIKey] = self._load_api_keys()
        self.audit_logs: List[AuditLog] = self._load_audit_logs()
        
        self._initialize_default_roles()

    def create_api_key(self, owner: str, name: str = "", scopes: List[str] = None,
                      expiry_days: int = None) -> str:
        """Create a new API key"""
        if expiry_days is None:
            expiry_days = governance_config.access.api_key_expiry_days
        
        # Generate secure random key
        actual_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(actual_key.encode()).hexdigest()
        
        from uuid import uuid4
        key_id = str(uuid4())
        
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            owner=owner,
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=expiry_days)).isoformat(),
            name=name or f"key-{key_id[:8]}",
            scopes=scopes or ["read"]
        )
        
        self.api_keys[key_id] = api_key
        self._save_api_keys()
        
        # Return the actual key (only shown once)
        return f"{key_id}:{actual_key}"

    def validate_api_key(self, key_id: str, key: str) -> bool:
        """Validate API key"""
        if key_id not in self.api_keys:
            return False
        
        api_key = self.api_keys[key_id]
        
        if not api_key.is_active:
            return False
        
        # Check expiry
        if datetime.fromisoformat(api_key.expires_at) < datetime.now():
            return False
        
        # Verify hash
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key_hash == api_key.key_hash

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        if key_id not in self.api_keys:
            return False
        
        self.api_keys[key_id].is_active = False
        self._save_api_keys()
        return True

    def grant_role(self, user: str, role: str) -> bool:
        """Grant role to user"""
        if role not in self.roles:
            return False
        
        # Store in users file (simplified)
        users_file = self.storage_path / f"user_{user}.json"
        user_data = {"user": user, "roles": [role], "assigned_at": datetime.now().isoformat()}
        
        try:
            with open(users_file, 'w') as f:
                json.dump(user_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error granting role: {e}")
            return False

    def check_permission(self, user: str, action: str, resource_type: str,
                        user_roles: List[str] = None) -> bool:
        """Check if user has permission for action"""
        if not user_roles:
            user_roles = self._get_user_roles(user)
        
        for role in user_roles:
            if role not in self.roles:
                continue
            
            for permission in self.roles[role]:
                if (permission.resource_type == resource_type and
                    (permission.action == action or permission.action == "admin")):
                    return True
        
        return False

    def log_audit_event(self, user: str, action: str, resource_type: str,
                       resource_id: str, status: str, changes: Dict = None,
                       ip_address: str = "", error_message: str = "") -> str:
        """Log an audit event"""
        from uuid import uuid4
        log_id = str(uuid4())
        
        audit_log = AuditLog(
            log_id=log_id,
            timestamp=datetime.now().isoformat(),
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            changes=changes or {},
            ip_address=ip_address,
            error_message=error_message
        )
        
        self.audit_logs.append(audit_log)
        self._save_audit_logs()
        
        return log_id

    def get_audit_logs(self, user: str = None, resource_id: str = None,
                      days: int = 30) -> List[AuditLog]:
        """Get audit logs with optional filters"""
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered = []
        
        for log in self.audit_logs:
            log_time = datetime.fromisoformat(log.timestamp)
            if log_time < cutoff_date:
                continue
            
            if user and log.user != user:
                continue
            
            if resource_id and log.resource_id != resource_id:
                continue
            
            filtered.append(log)
        
        return filtered

    def export_audit_logs(self, export_path: str, user: str = None,
                         days: int = 30) -> bool:
        """Export audit logs to JSON"""
        try:
            logs = self.get_audit_logs(user=user, days=days)
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "filters": {"user": user, "days": days},
                "total_logs": len(logs),
                "logs": [asdict(log) for log in logs]
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting audit logs: {e}")
            return False

    def get_access_report(self) -> Dict:
        """Generate access control report"""
        # Count API keys by status
        active_keys = sum(1 for k in self.api_keys.values() if k.is_active)
        expired_keys = sum(1 for k in self.api_keys.values()
                          if datetime.fromisoformat(k.expires_at) < datetime.now())
        
        # Count audit logs by status
        success_count = sum(1 for log in self.audit_logs if log.status == "success")
        failure_count = sum(1 for log in self.audit_logs if log.status == "failure")
        denied_count = sum(1 for log in self.audit_logs if log.status == "denied")
        
        # Most active users
        user_activity = {}
        for log in self.audit_logs:
            user_activity[log.user] = user_activity.get(log.user, 0) + 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "api_keys": {
                "total": len(self.api_keys),
                "active": active_keys,
                "expired": expired_keys
            },
            "audit_logs": {
                "total": len(self.audit_logs),
                "successful": success_count,
                "failed": failure_count,
                "denied": denied_count
            },
            "defined_roles": list(self.roles.keys()),
            "most_active_users": sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        }

    def _initialize_default_roles(self):
        """Initialize default roles and permissions"""
        if self.roles_file.exists():
            return  # Already initialized
        
        default_roles = {
            "admin": [
                RolePermission("admin", "asset", "admin"),
                RolePermission("admin", "catalog", "admin"),
                RolePermission("admin", "policy", "admin"),
                RolePermission("admin", "audit", "read"),
            ],
            "data_owner": [
                RolePermission("data_owner", "asset", "write", asset_level=True),
                RolePermission("data_owner", "catalog", "write", asset_level=True),
                RolePermission("data_owner", "lineage", "read"),
            ],
            "data_steward": [
                RolePermission("data_steward", "catalog", "write"),
                RolePermission("data_steward", "quality", "write"),
                RolePermission("data_steward", "lineage", "read"),
            ],
            "analyst": [
                RolePermission("analyst", "asset", "read"),
                RolePermission("analyst", "catalog", "read"),
                RolePermission("analyst", "lineage", "read"),
                RolePermission("analyst", "api", "read"),
            ],
            "viewer": [
                RolePermission("viewer", "asset", "read"),
                RolePermission("viewer", "catalog", "read"),
            ]
        }
        
        self.roles = {role: set(perms) for role, perms in default_roles.items()}
        self._save_roles()

    def _get_user_roles(self, user: str) -> List[str]:
        """Get user roles"""
        user_file = self.storage_path / f"user_{user}.json"
        if not user_file.exists():
            return []
        
        try:
            with open(user_file, 'r') as f:
                data = json.load(f)
                return data.get("roles", [])
        except Exception:
            return []

    def _load_roles(self) -> Dict[str, Set[RolePermission]]:
        """Load roles from storage"""
        if not self.roles_file.exists():
            return {}
        
        try:
            with open(self.roles_file, 'r') as f:
                data = json.load(f)
                return {role: set(RolePermission(**perm) for perm in perms)
                       for role, perms in data.items()}
        except Exception as e:
            print(f"Error loading roles: {e}")
            return {}

    def _load_api_keys(self) -> Dict[str, APIKey]:
        """Load API keys from storage"""
        if not self.api_keys_file.exists():
            return {}
        
        try:
            with open(self.api_keys_file, 'r') as f:
                data = json.load(f)
                return {kid: APIKey(**kdata) for kid, kdata in data.items()}
        except Exception as e:
            print(f"Error loading API keys: {e}")
            return {}

    def _load_audit_logs(self) -> List[AuditLog]:
        """Load audit logs from storage"""
        if not self.audit_logs_file.exists():
            return []
        
        try:
            with open(self.audit_logs_file, 'r') as f:
                data = json.load(f)
                return [AuditLog(**log_data) for log_data in data]
        except Exception as e:
            print(f"Error loading audit logs: {e}")
            return []

    def _save_roles(self):
        """Save roles to storage"""
        try:
            data = {role: [asdict(perm) for perm in perms]
                   for role, perms in self.roles.items()}
            with open(self.roles_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving roles: {e}")

    def _save_api_keys(self):
        """Save API keys to storage"""
        try:
            data = {kid: asdict(key) for kid, key in self.api_keys.items()}
            with open(self.api_keys_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving API keys: {e}")

    def _save_audit_logs(self):
        """Save audit logs to storage (keep only recent)"""
        try:
            # Keep only last 90 days of logs to avoid huge files
            cutoff_date = datetime.now() - timedelta(days=90)
            filtered_logs = [log for log in self.audit_logs
                           if datetime.fromisoformat(log.timestamp) >= cutoff_date]
            
            with open(self.audit_logs_file, 'w') as f:
                json.dump([asdict(log) for log in filtered_logs], f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving audit logs: {e}")


# Global access control instance
_access_manager = None

def get_access_manager() -> AccessControlManager:
    """Get or create global access control manager"""
    global _access_manager
    if _access_manager is None:
        _access_manager = AccessControlManager()
    return _access_manager
