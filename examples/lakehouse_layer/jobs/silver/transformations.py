"""
Silver Layer Transformation Job
Cleans and enriches Bronze data into Silver layer
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configs.lakehouse_config import lakehouse_config
from configs.logging_config import setup_logging, LogContext
from utils.delta_utils import DeltaLakeManager
from utils.quality_checks import DataQualityChecker


logger = setup_logging(__name__, lakehouse_config.log_level)


class SilverTransformationJob:
    """Transforms Bronze data into clean Silver layer tables"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.config = lakehouse_config
        self.delta_manager = DeltaLakeManager(spark)
        self.quality_checker = DataQualityChecker()
        self.logger = logger
    
    def transform_app_events(self) -> Dict[str, Any]:
        """Transform Bronze app events to Silver"""
        operation = 'app_events_bronze_to_silver'
        
        with LogContext(self.logger, operation):
            try:
                # Read from Bronze
                bronze_path = self.config.get_bronze_table_path('app_events')
                self.logger.info(f"📖 Reading from Bronze: {bronze_path}")
                
                df = self.delta_manager.read_delta_table('app_events', 'bronze')
                
                # Transform
                df = df.withColumn('event_date', F.to_date(F.col('event_timestamp'))) \
                       .withColumn('event_hour', F.hour(F.col('event_timestamp'))) \
                       .withColumn('is_valid', F.col('event_id').isNotNull()) \
                       .withColumn('processed_timestamp', F.current_timestamp())
                
                # Deduplication
                window_spec = Window.partitionBy('event_id').orderBy(F.desc('load_timestamp'))
                df = df.withColumn('row_num', F.row_number().over(window_spec)) \
                       .filter(F.col('row_num') == 1) \
                       .drop('row_num')
                
                self.logger.info(f"✅ Transformed {df.count()} records")
                
                # Write to Silver
                return self.delta_manager.write_delta_table(
                    df=df,
                    table_name='app_events',
                    layer='silver',
                    mode='append',
                    partition_by=['event_date'],
                    z_order_by=['user_id', 'event_timestamp'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to transform app events: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def transform_clickstream(self) -> Dict[str, Any]:
        """Transform Bronze clickstream to Silver with session analysis"""
        operation = 'clickstream_bronze_to_silver'
        
        with LogContext(self.logger, operation):
            try:
                # Read from Bronze
                self.logger.info(f"📖 Reading from Bronze clickstream")
                
                df = self.delta_manager.read_delta_table('clickstream', 'bronze')
                
                # Enrich with session metrics
                window_spec = Window.partitionBy('session_id').orderBy('click_timestamp')
                
                df = df.withColumn(
                    'session_start_time',
                    F.first('click_timestamp').over(
                        Window.partitionBy('session_id').orderBy('click_timestamp')
                    )
                ) \
                .withColumn(
                    'session_end_time',
                    F.last('click_timestamp').over(
                        Window.partitionBy('session_id').orderBy('click_timestamp')
                    )
                ) \
                .withColumn(
                    'click_position',
                    F.row_number().over(window_spec)
                )
                
                # Create session summary
                session_summary = df.groupBy('session_id', 'user_id', 'session_start_time', 'session_end_time') \
                    .agg(
                        F.collect_list('page_name').alias('page_sequence'),
                        F.count('*').alias('total_clicks'),
                        F.lit(True).alias('is_completed'),
                        (F.unix_timestamp('session_end_time') - F.unix_timestamp('session_start_time')).alias('session_duration_seconds'),
                    ) \
                    .withColumn('processed_timestamp', F.current_timestamp())
                
                self.logger.info(f"✅ Transformed {session_summary.count()} sessions")
                
                # Write to Silver
                return self.delta_manager.write_delta_table(
                    df=session_summary,
                    table_name='clickstream',
                    layer='silver',
                    mode='append',
                    z_order_by=['session_id', 'user_id'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to transform clickstream: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def build_users_dimension(self) -> Dict[str, Any]:
        """Build Silver users dimension table from app events"""
        operation = 'users_dimension_silver'
        
        with LogContext(self.logger, operation):
            try:
                # Read from Silver app events
                self.logger.info(f"📖 Reading from Silver app_events")
                
                events_df = self.delta_manager.read_delta_table('app_events', 'silver')
                
                # Build users dimension
                users_df = events_df.groupBy('user_id') \
                    .agg(
                        F.min('event_date').alias('first_seen_date'),
                        F.max('event_date').alias('last_seen_date'),
                        F.count('event_id').alias('total_events'),
                        F.countDistinct('session_id').alias('total_sessions'),
                        F.lit(True).alias('is_active'),
                    ) \
                    .withColumn('processed_timestamp', F.current_timestamp())
                
                self.logger.info(f"✅ Built users dimension with {users_df.count()} users")
                
                # Write to Silver
                return self.delta_manager.write_delta_table(
                    df=users_df,
                    table_name='users',
                    layer='silver',
                    mode='overwrite',
                    z_order_by=['user_id'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to build users dimension: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def run(self) -> Dict[str, Any]:
        """Run all Silver transformation jobs"""
        self.logger.info("=" * 80)
        self.logger.info("🥈 SILVER LAYER TRANSFORMATION JOB")
        self.logger.info("=" * 80)
        
        results = {
            'job_name': 'silver_transformation',
            'start_timestamp': datetime.utcnow().isoformat(),
            'transformations': {},
        }
        
        # Transform all data sources
        results['transformations']['app_events'] = self.transform_app_events()
        results['transformations']['clickstream'] = self.transform_clickstream()
        results['transformations']['users_dimension'] = self.build_users_dimension()
        
        results['end_timestamp'] = datetime.utcnow().isoformat()
        
        # Summary
        self.logger.info("=" * 80)
        self.logger.info(f"✅ SILVER TRANSFORMATION COMPLETE")
        self.logger.info(f"   Transformations: {len(results['transformations'])}")
        self.logger.info("=" * 80)
        
        return results


def create_spark_session() -> SparkSession:
    """Create Spark session with Delta Lake support"""
    return SparkSession.builder \
        .appName('silver-transformation-job') \
        .master(lakehouse_config.spark_master) \
        .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension') \
        .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog') \
        .config('spark.jars.packages', 'io.delta:delta-core_2.12:2.4.0') \
        .getOrCreate()


if __name__ == '__main__':
    spark = create_spark_session()
    
    try:
        job = SilverTransformationJob(spark)
        results = job.run()
        
        # Log results
        logger.info(f"Results: {results}")
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        spark.stop()
