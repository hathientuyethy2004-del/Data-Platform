"""
Gold Layer Aggregation Job
Creates business-ready aggregated and summarized tables
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


logger = setup_logging(__name__, lakehouse_config.log_level)


class GoldAggregationJob:
    """Creates business-ready Gold layer aggregations"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.config = lakehouse_config
        self.delta_manager = DeltaLakeManager(spark)
        self.logger = logger
    
    def aggregate_event_metrics(self) -> Dict[str, Any]:
        """Create hourly event metrics in Gold layer"""
        operation = 'event_metrics_aggregation'
        
        with LogContext(self.logger, operation):
            try:
                # Read from Silver
                events_df = self.delta_manager.read_delta_table('app_events', 'silver')
                
                # Create hourly metrics
                metrics_df = events_df.groupBy(
                    F.to_date('event_timestamp').alias('metric_date'),
                    F.hour('event_timestamp').alias('metric_hour'),
                    'event_type',
                    'app_type'
                ).agg(
                    F.count('event_id').alias('total_events'),
                    F.countDistinct('user_id').alias('unique_users'),
                    F.avg('event_value').alias('avg_event_value'),
                    F.max('event_value').alias('max_event_value'),
                    F.min('event_value').alias('min_event_value'),
                )
                
                self.logger.info(f"✅ Created {metrics_df.count()} hourly metrics")
                
                # Write to Gold
                return self.delta_manager.write_delta_table(
                    df=metrics_df,
                    table_name='event_metrics',
                    layer='gold',
                    mode='overwrite',
                    partition_by=['metric_date'],
                    z_order_by=['event_type', 'app_type'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to aggregate event metrics: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def create_user_segments(self) -> Dict[str, Any]:
        """Create user segments based on engagement and behavior"""
        operation = 'user_segmentation'
        
        with LogContext(self.logger, operation):
            try:
                # Read from Silver users
                users_df = self.delta_manager.read_delta_table('users', 'silver')
                
                # Calculate engagement metrics
                segments_df = users_df.withColumn(
                    'engagement_score',
                    (F.col('total_events') / F.max('total_events').over(Window.partitionBy()) * 100)
                ) \
                .withColumn(
                    'segment_name',
                    F.when(F.col('engagement_score') >= 80, 'VIP')
                     .when(F.col('engagement_score') >= 50, 'Active')
                     .when(F.col('engagement_score') >= 20, 'Regular')
                     .otherwise('Inactive')
                ) \
                .withColumn('risk_of_churn', 100 - F.col('engagement_score')) \
                .withColumn('segment_date', F.current_date()) \
                .withColumn('updated_timestamp', F.current_timestamp())
                
                self.logger.info(f"✅ Segmented {segments_df.count()} users")
                
                # Write to Gold
                return self.delta_manager.write_delta_table(
                    df=segments_df,
                    table_name='user_segments',
                    layer='gold',
                    mode='overwrite',
                    partition_by=['segment_date'],
                    z_order_by=['segment_name'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to create user segments: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def create_daily_summary(self) -> Dict[str, Any]:
        """Create daily summary metrics"""
        operation = 'daily_summary'
        
        with LogContext(self.logger, operation):
            try:
                # Read from Silver events and users
                events_df = self.delta_manager.read_delta_table('app_events', 'silver')
                users_df = self.delta_manager.read_delta_table('users', 'silver')
                
                # Daily event aggregates
                daily_events = events_df.groupBy(
                    F.to_date('event_timestamp').alias('summary_date')
                ).agg(
                    F.count('event_id').alias('total_events'),
                    F.countDistinct('user_id').alias('total_users'),
                )
                
                # Daily user metrics
                daily_users = users_df.groupBy(
                    F.to_date('processed_timestamp').alias('summary_date')
                ).agg(
                    F.count('user_id').alias('new_users'),
                )
                
                # Combine
                summary_df = daily_events.join(daily_users, 'summary_date', 'left') \
                    .fillna(0) \
                    .withColumn('total_sessions', F.lit(0))  # TODO: Calculate from clickstream \
                    .withColumn('avg_session_duration', F.lit(0.0)) \
                    .withColumn('bounce_rate', F.lit(0.0)) \
                    .withColumn('return_user_percentage', F.lit(0.0)) \
                    .withColumn('processed_timestamp', F.current_timestamp())
                
                self.logger.info(f"✅ Created daily summaries for {summary_df.count()} days")
                
                # Write to Gold
                return self.delta_manager.write_delta_table(
                    df=summary_df,
                    table_name='daily_summary',
                    layer='gold',
                    mode='overwrite',
                    partition_by=['summary_date'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to create daily summary: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def create_hourly_metrics(self) -> Dict[str, Any]:
        """Create hourly operational metrics"""
        operation = 'hourly_metrics'
        
        with LogContext(self.logger, operation):
            try:
                # Read from Silver events
                events_df = self.delta_manager.read_delta_table('app_events', 'silver')
                
                # Hourly metrics
                hourly_df = events_df.groupBy(
                    F.to_date('event_timestamp').alias('metric_date'),
                    F.hour('event_timestamp').alias('metric_hour')
                ).agg(
                    F.count('event_id').alias('total_events'),
                    F.countDistinct('user_id').alias('unique_users'),
                    F.lit(0).alias('total_sessions'),
                    F.lit(0.0).alias('avg_response_time_ms'),
                    F.lit(0).alias('error_count'),
                    F.current_timestamp().alias('processed_timestamp'),
                )
                
                self.logger.info(f"✅ Created hourly metrics for {hourly_df.count()} hours")
                
                # Write to Gold
                return self.delta_manager.write_delta_table(
                    df=hourly_df,
                    table_name='hourly_metrics',
                    layer='gold',
                    mode='overwrite',
                    partition_by=['metric_date'],
                    z_order_by=['metric_hour'],
                )
            
            except Exception as e:
                self.logger.error(f"Failed to create hourly metrics: {e}")
                return {'status': 'failed', 'error': str(e), 'operation': operation}
    
    def run(self) -> Dict[str, Any]:
        """Run all Gold aggregation jobs"""
        self.logger.info("=" * 80)
        self.logger.info("🏆 GOLD LAYER AGGREGATION JOB")
        self.logger.info("=" * 80)
        
        results = {
            'job_name': 'gold_aggregation',
            'start_timestamp': datetime.utcnow().isoformat(),
            'aggregations': {},
        }
        
        # Create all Gold tables
        results['aggregations']['event_metrics'] = self.aggregate_event_metrics()
        results['aggregations']['user_segments'] = self.create_user_segments()
        results['aggregations']['daily_summary'] = self.create_daily_summary()
        results['aggregations']['hourly_metrics'] = self.create_hourly_metrics()
        
        results['end_timestamp'] = datetime.utcnow().isoformat()
        
        # Summary
        self.logger.info("=" * 80)
        self.logger.info(f"✅ GOLD AGGREGATION COMPLETE")
        self.logger.info(f"   Aggregations: {len(results['aggregations'])}")
        self.logger.info("=" * 80)
        
        return results


def create_spark_session() -> SparkSession:
    """Create Spark session with Delta Lake support"""
    return SparkSession.builder \
        .appName('gold-aggregation-job') \
        .master(lakehouse_config.spark_master) \
        .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension') \
        .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog') \
        .config('spark.jars.packages', 'io.delta:delta-core_2.12:2.4.0') \
        .getOrCreate()


if __name__ == '__main__':
    spark = create_spark_session()
    
    try:
        job = GoldAggregationJob(spark)
        results = job.run()
        
        # Log results
        logger.info(f"Results: {results}")
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        spark.stop()
