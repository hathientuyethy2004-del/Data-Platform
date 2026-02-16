"""
Lakehouse Configuration
Manages Delta Lake paths, retention policies, and data organization settings
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List
from pathlib import Path


@dataclass
class DeltaLakeConfig:
    """Delta Lake configuration"""
    # Enable Delta Lake features
    enable_delta: bool = True
    # ACID guarantees
    enable_transaction_log: bool = True
    # Optimize writes
    auto_optimize: bool = True
    # Retention policies (days)
    time_travel_retention_days: int = 30
    # Vacuum settings (days)
    vacuum_retention_days: int = 7
    # Z-order columns for optimization
    z_order_columns: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class StorageConfig:
    """Storage configuration for lakehouse"""
    # Base lakehouse path
    lakehouse_base_path: str = "/var/lib/lakehouse"
    
    # Layer paths
    bronze_path: str = "/var/lib/lakehouse/bronze"
    silver_path: str = "/var/lib/lakehouse/silver"
    gold_path: str = "/var/lib/lakehouse/gold"
    
    # Temporary/staging paths
    staging_path: str = "/var/lib/lakehouse/staging"
    archive_path: str = "/var/lib/lakehouse/archive"
    
    # Partition strategy
    partition_strategy: str = "date"  # date, hour, none
    
    # Compression
    compression_codec: str = "snappy"  # snappy, gzip, lz4, uncompressed
    
    def __post_init__(self):
        # Create directories if they don't exist
        for path_attr in ['lakehouse_base_path', 'bronze_path', 'silver_path', 
                         'gold_path', 'staging_path', 'archive_path']:
            path_value = getattr(self, path_attr)
            Path(path_value).mkdir(parents=True, exist_ok=True)


@dataclass
class DataQualityConfig:
    """Data quality checks configuration"""
    # Enable quality checks
    enable_quality_checks: bool = True
    # Maximum null percentage allowed (%)
    max_null_percentage: float = 5.0
    # Enable duplicate detection
    check_duplicates: bool = True
    # Enable schema validation
    validate_schema: bool = True
    # Quality check failure action
    failure_action: str = "log"  # log, warn, fail


@dataclass
class RetentionPolicy:
    """Data retention policy"""
    # Table name
    table_name: str = ""
    # Retention days from creation
    retention_days: int = 365
    # Archive before deleting
    archive_before_delete: bool = True
    # Delete old partitions
    delete_old_partitions: bool = True


class LakehouseConfig:
    """Main Lakehouse Configuration Manager"""
    
    def __init__(self):
        # Storage configuration
        self.storage = StorageConfig(
            lakehouse_base_path=os.getenv('LAKEHOUSE_BASE_PATH', '/var/lib/lakehouse'),
            bronze_path=os.getenv('BRONZE_PATH', '/var/lib/lakehouse/bronze'),
            silver_path=os.getenv('SILVER_PATH', '/var/lib/lakehouse/silver'),
            gold_path=os.getenv('GOLD_PATH', '/var/lib/lakehouse/gold'),
            staging_path=os.getenv('STAGING_PATH', '/var/lib/lakehouse/staging'),
            archive_path=os.getenv('ARCHIVE_PATH', '/var/lib/lakehouse/archive'),
        )
        
        # Delta Lake configuration
        self.delta = DeltaLakeConfig(
            enable_delta=os.getenv('ENABLE_DELTA', 'true').lower() == 'true',
            auto_optimize=os.getenv('AUTO_OPTIMIZE', 'true').lower() == 'true',
            time_travel_retention_days=int(os.getenv('TIME_TRAVEL_RETENTION_DAYS', '30')),
            vacuum_retention_days=int(os.getenv('VACUUM_RETENTION_DAYS', '7')),
        )
        
        # Data quality configuration
        self.quality = DataQualityConfig(
            enable_quality_checks=os.getenv('ENABLE_QUALITY_CHECKS', 'true').lower() == 'true',
            max_null_percentage=float(os.getenv('MAX_NULL_PERCENTAGE', '5.0')),
            check_duplicates=os.getenv('CHECK_DUPLICATES', 'true').lower() == 'true',
            validate_schema=os.getenv('VALIDATE_SCHEMA', 'true').lower() == 'true',
            failure_action=os.getenv('QUALITY_FAILURE_ACTION', 'log'),
        )
        
        # Spark configuration
        self.spark_master = os.getenv('SPARK_MASTER', 'spark://spark-master:7077')
        self.spark_app_name = os.getenv('SPARK_APP_NAME', 'lakehouse-layer')
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.logs_dir = os.getenv('LOGS_DIR', '/var/lib/lakehouse/logs')
        
        # Processing configuration
        self.processing_layer_outputs = os.getenv(
            'PROCESSING_LAYER_OUTPUTS',
            '/workspaces/Data-Platform/processing_layer/outputs'
        )
    
    def get_bronze_table_path(self, table_name: str) -> str:
        """Get Bronze layer path for a table"""
        return f"{self.storage.bronze_path}/{table_name}"
    
    def get_silver_table_path(self, table_name: str) -> str:
        """Get Silver layer path for a table"""
        return f"{self.storage.silver_path}/{table_name}"
    
    def get_gold_table_path(self, table_name: str) -> str:
        """Get Gold layer path for a table"""
        return f"{self.storage.gold_path}/{table_name}"
    
    def get_staging_path(self, table_name: str) -> str:
        """Get staging path for temporary processing"""
        return f"{self.storage.staging_path}/{table_name}"
    
    def get_retention_policy(self, table_name: str) -> RetentionPolicy:
        """Get retention policy for a table"""
        # Default retention policies
        policies = {
            'app_events': RetentionPolicy('app_events', retention_days=365),
            'clickstream': RetentionPolicy('clickstream', retention_days=180),
            'user_segments': RetentionPolicy('user_segments', retention_days=30),
            'hourly_aggregates': RetentionPolicy('hourly_aggregates', retention_days=90),
            'daily_summaries': RetentionPolicy('daily_summaries', retention_days=365),
        }
        return policies.get(table_name, RetentionPolicy(table_name, retention_days=365))
    
    def get_z_order_columns(self, table_name: str) -> List[str]:
        """Get Z-order columns for table optimization"""
        z_orders = {
            'app_events': ['user_id', 'event_date', 'app_type'],
            'clickstream': ['session_id', 'timestamp', 'user_id'],
            'user_segments': ['user_id', 'segment_date'],
            'hourly_aggregates': ['event_date', 'hour'],
            'daily_summaries': ['summary_date'],
        }
        return z_orders.get(table_name, ['timestamp'] if 'timestamp' in table_name else [])
    
    def get_spark_session_config(self) -> Dict[str, str]:
        """Get Spark session configuration for Delta Lake"""
        return {
            'spark.sql.extensions': 'io.delta.sql.DeltaSparkSessionExtension',
            'spark.sql.catalog.spark_catalog': 'org.apache.spark.sql.delta.catalog.DeltaCatalog',
            'spark.delta.logStore.class': 'org.apache.spark.sql.delta.storage.LogStoreProvider',
            'spark.databricks.delta.schema.autoMerge.enabled': 'true',
            'spark.databricks.delta.optimizeWrite.enabled': 'true',
            'spark.databricks.delta.autoCompact.enabled': 'true',
        }


# Global configuration instance
lakehouse_config = LakehouseConfig()
