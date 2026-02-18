"""
Delta Lake Utilities
Provides functions for working with Delta Lake tables
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType
from configs.lakehouse_config import lakehouse_config
from configs.logging_config import setup_logging, LogContext


logger = setup_logging(__name__)


class DeltaLakeManager:
    """Manager for Delta Lake operations"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.logger = logger
        
        # Configure Delta Lake
        for key, value in lakehouse_config.get_spark_session_config().items():
            spark.conf.set(key, value)
    
    def write_delta_table(
        self,
        df: DataFrame,
        table_name: str,
        layer: str,  # bronze, silver, gold
        mode: str = 'overwrite',
        partition_by: Optional[List[str]] = None,
        z_order_by: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Write DataFrame to Delta Lake table
        
        Args:
            df: Input DataFrame
            table_name: Name of the table
            layer: Lakehouse layer (bronze, silver, gold)
            mode: Write mode (overwrite, append, ignore, error)
            partition_by: Columns to partition by
            z_order_by: Columns to Z-order optimize
        
        Returns:
            Dictionary with operation result and metadata
        """
        operation_context = f"{layer}.{table_name}"
        
        with LogContext(self.logger, f"write_delta_table {operation_context}"):
            # Determine table path
            if layer == 'bronze':
                table_path = lakehouse_config.get_bronze_table_path(table_name)
            elif layer == 'silver':
                table_path = lakehouse_config.get_silver_table_path(table_name)
            elif layer == 'gold':
                table_path = lakehouse_config.get_gold_table_path(table_name)
            else:
                raise ValueError(f"Invalid layer: {layer}")
            
            self.logger.info(f"📝 Writing to Delta table at: {table_path}")
            self.logger.info(f"   Records: {df.count()}, Schema: {df.columns}")
            
            # Write DataFrame
            writer = df.write.format('delta').mode(mode)
            
            if partition_by:
                writer = writer.partitionBy(*partition_by)
                self.logger.info(f"   Partitioned by: {partition_by}")
            
            writer.option('path', table_path).save()
            
            # Optimize table if Z-order columns provided
            if z_order_by and (mode in ['overwrite', 'append']):
                try:
                    z_order_cols = ','.join(z_order_by)
                    self.spark.sql(f"OPTIMIZE delta.`{table_path}` ZORDER BY ({z_order_cols})")
                    self.logger.info(f"   Optimized with Z-order: {z_order_by}")
                except Exception as e:
                    self.logger.warning(f"   Z-order optimization failed: {e}")
            
            return {
                'status': 'success',
                'table_path': table_path,
                'layer': layer,
                'table_name': table_name,
                'record_count': df.count(),
                'timestamp': datetime.utcnow().isoformat(),
            }
    
    def read_delta_table(
        self,
        table_name: str,
        layer: str,
        version: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> DataFrame:
        """
        Read Delta Lake table with optional time travel
        
        Args:
            table_name: Name of the table
            layer: Lakehouse layer (bronze, silver, gold)
            version: Specific version to read (Delta time travel)
            timestamp: Timestamp string to read at (Delta time travel)
        
        Returns:
            DataFrame read from Delta table
        """
        # Determine table path
        if layer == 'bronze':
            table_path = lakehouse_config.get_bronze_table_path(table_name)
        elif layer == 'silver':
            table_path = lakehouse_config.get_silver_table_path(table_name)
        elif layer == 'gold':
            table_path = lakehouse_config.get_gold_table_path(table_name)
        else:
            raise ValueError(f"Invalid layer: {layer}")
        
        self.logger.info(f"📖 Reading from Delta table: {table_path}")
        
        # Read with optional time travel
        reader = self.spark.read.format('delta')
        
        if version is not None:
            reader = reader.option('versionAsOf', version)
            self.logger.info(f"   Version: {version}")
        elif timestamp is not None:
            reader = reader.option('timestampAsOf', timestamp)
            self.logger.info(f"   Timestamp: {timestamp}")
        
        df = reader.option('path', table_path).load()
        self.logger.info(f"   Records: {df.count()}, Columns: {len(df.columns)}")
        
        return df
    
    def get_table_metadata(self, table_name: str, layer: str) -> Dict[str, Any]:
        """
        Get metadata about a Delta table
        
        Args:
            table_name: Name of the table
            layer: Lakehouse layer
        
        Returns:
            Dictionary with table metadata
        """
        if layer == 'bronze':
            table_path = lakehouse_config.get_bronze_table_path(table_name)
        elif layer == 'silver':
            table_path = lakehouse_config.get_silver_table_path(table_name)
        elif layer == 'gold':
            table_path = lakehouse_config.get_gold_table_path(table_name)
        else:
            raise ValueError(f"Invalid layer: {layer}")
        
        try:
            # Read table history
            history = self.spark.sql(f"DESCRIBE HISTORY delta.`{table_path}`")
            
            return {
                'table_name': table_name,
                'layer': layer,
                'path': table_path,
                'num_versions': history.count(),
                'schema': [{'name': field.name, 'type': str(field.dataType)} 
                          for field in self.read_delta_table(table_name, layer).schema],
            }
        except Exception as e:
            self.logger.error(f"Failed to get metadata for {table_name}: {e}")
            return {'error': str(e)}
    
    def vacuum_table(self, table_name: str, layer: str, retention_hours: int = 168) -> None:
        """
        Vacuum Delta table to remove old files
        
        Args:
            table_name: Name of the table
            layer: Lakehouse layer
            retention_hours: Hours to retain files (default 7 days)
        """
        if layer == 'bronze':
            table_path = lakehouse_config.get_bronze_table_path(table_name)
        elif layer == 'silver':
            table_path = lakehouse_config.get_silver_table_path(table_name)
        elif layer == 'gold':
            table_path = lakehouse_config.get_gold_table_path(table_name)
        else:
            raise ValueError(f"Invalid layer: {layer}")
        
        with LogContext(self.logger, f"vacuum_table {table_name}"):
            self.spark.sql(f"VACUUM delta.`{table_path}` RETAIN {retention_hours} HOURS")
            self.logger.info(f"✅ Vacuumed {table_name}")
    
    def optimize_table(self, table_name: str, layer: str) -> None:
        """
        Optimize Delta table
        
        Args:
            table_name: Name of the table
            layer: Lakehouse layer
        """
        if layer == 'bronze':
            table_path = lakehouse_config.get_bronze_table_path(table_name)
        elif layer == 'silver':
            table_path = lakehouse_config.get_silver_table_path(table_name)
        elif layer == 'gold':
            table_path = lakehouse_config.get_gold_table_path(table_name)
        else:
            raise ValueError(f"Invalid layer: {layer}")
        
        with LogContext(self.logger, f"optimize_table {table_name}"):
            stats = self.spark.sql(f"OPTIMIZE delta.`{table_path}`").collect()
            self.logger.info(f"✅ Optimized {table_name}")
    
    def create_or_replace_view(
        self,
        view_name: str,
        df: DataFrame,
        is_temp: bool = False,
    ) -> None:
        """
        Create or replace a view
        
        Args:
            view_name: Name of the view
            df: DataFrame to create view from
            is_temp: Whether to create temporary view
        """
        view_type = 'TEMPORARY' if is_temp else 'TEMPORARY'
        
        if is_temp:
            df.createOrReplaceTempView(view_name)
        else:
            df.createOrReplaceGlobalTempView(view_name)
        
        self.logger.info(f"📌 Created view: {view_name}")


class SchemaValidator:
    """Validates and manages schemas for lakehouse tables"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.logger = logger
    
    def validate_schema(self, df: DataFrame, expected_schema: StructType) -> bool:
        """
        Validate DataFrame schema against expected schema
        
        Args:
            df: DataFrame to validate
            expected_schema: Expected schema
        
        Returns:
            True if schema matches, False otherwise
        """
        actual_schema = df.schema
        
        if len(actual_schema) != len(expected_schema):
            self.logger.warning(
                f"Schema mismatch: expected {len(expected_schema)} columns, "
                f"got {len(actual_schema)}"
            )
            return False
        
        for expected_field, actual_field in zip(expected_schema, actual_schema):
            if expected_field.name != actual_field.name:
                self.logger.warning(
                    f"Column name mismatch: expected '{expected_field.name}', "
                    f"got '{actual_field.name}'"
                )
                return False
            
            if str(expected_field.dataType) != str(actual_field.dataType):
                self.logger.warning(
                    f"Column type mismatch for '{expected_field.name}': "
                    f"expected {expected_field.dataType}, "
                    f"got {actual_field.dataType}"
                )
                return False
        
        return True
