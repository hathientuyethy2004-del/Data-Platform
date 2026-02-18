"""
Bronze Layer Ingestion Job
Reads raw data from processing layer and stores in Bronze layer
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from configs.lakehouse_config import lakehouse_config
from configs.logging_config import setup_logging, LogContext
from utils.delta_utils import DeltaLakeManager
from utils.schemas import (
    BRONZE_APP_EVENTS_SCHEMA,
    BRONZE_CLICKSTREAM_SCHEMA,
    BRONZE_CDC_SCHEMA,
)
from utils.quality_checks import DataQualityChecker


logger = setup_logging(__name__, lakehouse_config.log_level)


class BronzeIngestionJob:
    """Ingests data from processing layer into Bronze layer Delta tables"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.config = lakehouse_config
        self.delta_manager = DeltaLakeManager(spark)
        self.quality_checker = DataQualityChecker()
        self.logger = logger
    
    def ingest_app_events(self) -> Dict[str, Any]:
        """Ingest app events from processing layer to Bronze"""
        operation = 'app_events_to_bronze'
        
        with LogContext(self.logger, operation):
            try:
                # Read from processing layer output
                processing_path = f"{self.config.processing_layer_outputs}/events_aggregated_realtime"
                
                self.logger.info(f"📖 Reading from: {processing_path}")
                
                df = self.spark.read.parquet(processing_path)
                
                if df.count() == 0:
                    self.logger.warning(f"No data found in {processing_path}")
                    return {
                        'status': 'skipped',
                        'reason': 'no_data',
                        'operation': operation,
                    }
                
                # Add load timestamp
                df = df.withColumn('load_timestamp', F.current_timestamp())
                df = df.withColumn('source_system', F.lit('processing_layer'))
                
                # Rename columns to match schema
                df = df.select(
                    F.col('event_id').alias('event_id'),
                    F.col('user_id').alias('user_id'),
                    F.col('event_type').alias('event_type'),
                    F.col('app_type').alias('app_type'),
                    F.col('event_timestamp').alias('event_timestamp'),
                    F.col('properties').cast('string').alias('event_properties'),
                    F.col('device_info').cast('string').alias('device_info'),
                    F.col('load_timestamp').alias('load_timestamp'),
                    F.col('source_system').alias('source_system'),
                )
                
                # Quality checks
                quality_results = self.quality_checker.run_all_checks(
                    df,
                    null_checks={
                        'event_id': 0.0,
                        'user_id': 0.1,
                        'event_timestamp': 0.0,
                    },
                    key_columns=['event_id'],
                )
                
                # Write to Bronze
                return self.delta_manager.write_delta_table(
                    df=df,
                    table_name='app_events',
                    layer='bronze',
                    mode='append',
                    partition_by=['event_timestamp_date'],
                    z_order_by=['user_id', 'event_timestamp'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to ingest app events: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def ingest_clickstream(self) -> Dict[str, Any]:
        """Ingest clickstream data from processing layer to Bronze"""
        operation = 'clickstream_to_bronze'
        
        with LogContext(self.logger, operation):
            try:
                # Read from processing layer output
                processing_path = f"{self.config.processing_layer_outputs}/clickstream_sessions"
                
                self.logger.info(f"📖 Reading from: {processing_path}")
                
                df = self.spark.read.parquet(processing_path)
                
                if df.count() == 0:
                    self.logger.warning(f"No data found in {processing_path}")
                    return {
                        'status': 'skipped',
                        'reason': 'no_data',
                        'operation': operation,
                    }
                
                # Add load timestamp
                df = df.withColumn('load_timestamp', F.current_timestamp())
                
                # Quality checks
                quality_results = self.quality_checker.run_all_checks(
                    df,
                    null_checks={
                        'click_id': 0.0,
                        'session_id': 0.0,
                        'click_timestamp': 0.0,
                    },
                    key_columns=['click_id'],
                )
                
                # Write to Bronze
                return self.delta_manager.write_delta_table(
                    df=df,
                    table_name='clickstream',
                    layer='bronze',
                    mode='append',
                    partition_by=['click_timestamp_date'],
                    z_order_by=['session_id', 'user_id'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to ingest clickstream data: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def ingest_cdc_changes(self) -> Dict[str, Any]:
        """Ingest CDC changes from processing layer to Bronze"""
        operation = 'cdc_to_bronze'
        
        with LogContext(self.logger, operation):
            try:
                # Read from processing layer output
                processing_path = f"{self.config.processing_layer_outputs}/cdc_transformed"
                
                self.logger.info(f"📖 Reading from: {processing_path}")
                
                df = self.spark.read.parquet(processing_path)
                
                if df.count() == 0:
                    self.logger.warning(f"No data found in {processing_path}")
                    return {
                        'status': 'skipped',
                        'reason': 'no_data',
                        'operation': operation,
                    }
                
                # Add load timestamp
                df = df.withColumn('load_timestamp', F.current_timestamp())
                
                # Quality checks
                quality_results = self.quality_checker.run_all_checks(
                    df,
                    null_checks={
                        'cdc_id': 0.0,
                        'table_name': 0.0,
                        'operation_type': 0.0,
                    },
                    key_columns=['cdc_id'],
                )
                
                # Write to Bronze
                return self.delta_manager.write_delta_table(
                    df=df,
                    table_name='cdc_changes',
                    layer='bronze',
                    mode='append',
                    partition_by=['timestamp_date'],
                    z_order_by=['table_name', 'timestamp'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to ingest CDC changes: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def run(self) -> Dict[str, Any]:
        """Run all Bronze ingestion jobs"""
        self.logger.info("=" * 80)
        self.logger.info("🥉 BRONZE LAYER INGESTION JOB")
        self.logger.info("=" * 80)
        
        results = {
            'job_name': 'bronze_ingestion',
            'start_timestamp': datetime.utcnow().isoformat(),
            'operations': {},
        }
        
        # Ingest all data sources
        results['operations']['app_events'] = self.ingest_app_events()
        results['operations']['clickstream'] = self.ingest_clickstream()
        results['operations']['cdc_changes'] = self.ingest_cdc_changes()
        
        results['end_timestamp'] = datetime.utcnow().isoformat()
        
        # Summary
        self.logger.info("=" * 80)
        self.logger.info(f"✅ BRONZE INGESTION COMPLETE")
        self.logger.info(f"   Operations: {len(results['operations'])}")
        self.logger.info("=" * 80)
        
        return results


def create_spark_session() -> SparkSession:
    """Create Spark session with Delta Lake support"""
    return SparkSession.builder \
        .appName('bronze-ingestion-job') \
        .master(lakehouse_config.spark_master) \
        .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension') \
        .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog') \
        .config('spark.jars.packages', 'io.delta:delta-core_2.12:2.4.0') \
        .getOrCreate()


if __name__ == '__main__':
    spark = create_spark_session()
    
    try:
        job = BronzeIngestionJob(spark)
        results = job.run()
        
        # Log results
        logger.info(f"Results: {results}")
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        spark.stop()
