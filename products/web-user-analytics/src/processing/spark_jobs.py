"""
Web User Analytics - Spark Jobs

Orchestrates Spark jobs for ingestion, transformation, and aggregation.
Handles scheduled batch processing of events through the data pipeline.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, to_timestamp, to_date, hour
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.storage.bronze_schema import (
    BRONZE_EVENT_SCHEMA, SILVER_PAGE_VIEW_SCHEMA, SILVER_SESSION_SCHEMA,
    GOLD_PAGE_METRICS_SCHEMA, GOLD_FUNNEL_METRICS_SCHEMA,
    GOLD_SESSION_METRICS_SCHEMA
)
from src.storage.silver_transforms import (
    BronzeToSilverTransformer, SilverAggregator, SilverValidator
)
from src.storage.gold_metrics import (
    GoldPageMetricsCalculator, GoldFunnelMetricsCalculator,
    GoldSessionMetricsCalculator, GoldUserJourneyCalculator,
    GoldConversionCalculator, GoldMetricsWriter
)


logger = logging.getLogger(__name__)


class SparkJobOrchestrator:
    """Orchestrates and manages Spark jobs"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize job orchestrator.
        
        Args:
            config: Job configuration dict
        """
        self.config = config
        self.spark = self._create_spark_session()
        self.transformer = BronzeToSilverTransformer(self.spark)
        self.aggregator = SilverAggregator(self.spark)
        self.validator = SilverValidator()
        
        # Initialize calculators
        self.page_calculator = GoldPageMetricsCalculator(self.spark)
        self.funnel_calculator = GoldFunnelMetricsCalculator(self.spark)
        self.session_calculator = GoldSessionMetricsCalculator(self.spark)
        self.user_calculator = GoldUserJourneyCalculator(self.spark)
        self.conversion_calculator = GoldConversionCalculator(self.spark)
        
        # Initialize writer
        self.writer = GoldMetricsWriter(self.spark, config.get("output_path", "/data/gold"))
    
    def _create_spark_session(self) -> SparkSession:
        """Create and configure Spark session"""
        return SparkSession.builder \
            .appName("web-user-analytics") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.shuffle.partitions", "200") \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .config("spark.databricks.delta.schema.autoMerge.enabled", "true") \
            .getOrCreate()
    
    def run_bronze_to_silver_job(self, 
                                bronze_path: str,
                                silver_path: str,
                                date_str: Optional[str] = None) -> Dict[str, int]:
        """
        Run Bronze to Silver transformation job.
        
        Args:
            bronze_path: Path to Bronze layer data
            silver_path: Path to Silver layer output
            date_str: Specific date to process (YYYY-MM-DD) or None for latest
            
        Returns:
            Dict with job statistics
        """
        logger.info(f"Starting Bronze to Silver job for {date_str or 'latest'}")
        
        stats = {"start_time": datetime.utcnow()}
        
        try:
            # Read Bronze events
            bronze_df = self.spark.read.format("delta").schema(BRONZE_EVENT_SCHEMA).load(
                bronze_path
            )
            
            if date_str:
                bronze_df = bronze_df.filter(to_date(col("timestamp")) == date_str)
            
            stats["bronze_records"] = bronze_df.count()
            logger.info(f"Read {stats['bronze_records']} Bronze records")
            
            # Transform to Silver
            silver_pv_df = self.transformer.clean_page_views(bronze_df)
            silver_pv_df = self.validator.validate_page_view(silver_pv_df)
            
            stats["silver_pv_records"] = silver_pv_df.count()
            stats["pv_quality"] = self.validator.get_data_quality_report(silver_pv_df)
            
            # Save Silver page views
            silver_pv_df.write.format("delta").mode("append") \
                .partitionBy("event_date", "event_hour") \
                .save(f"{silver_path}/page_views")
            
            logger.info(f"Wrote {stats['silver_pv_records']} Silver page view records")
            
            # Transform sessions
            silver_sessions_df = self.transformer.reconstruct_sessions(bronze_df)
            silver_sessions_df = self.validator.validate_session(silver_sessions_df)
            
            stats["silver_session_records"] = silver_sessions_df.count()
            
            # Save Silver sessions
            silver_sessions_df.write.format("delta").mode("append") \
                .partitionBy("event_date", "event_hour") \
                .save(f"{silver_path}/sessions")
            
            logger.info(f"Wrote {stats['silver_session_records']} Silver session records")
            
            stats["status"] = "success"
            
        except Exception as e:
            logger.error(f"Bronze to Silver job failed: {e}", exc_info=True)
            stats["status"] = "failed"
            stats["error"] = str(e)
        
        finally:
            stats["end_time"] = datetime.utcnow()
        
        return stats
    
    def run_silver_to_gold_job(self,
                              silver_path: str,
                              gold_path: str,
                              date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Run Silver to Gold aggregation job.
        
        Args:
            silver_path: Path to Silver layer data
            gold_path: Path to Gold layer output
            date_str: Specific date to process or None for all
            
        Returns:
            Dict with job statistics
        """
        logger.info(f"Starting Silver to Gold job for {date_str or 'all'}")
        
        stats = {"start_time": datetime.utcnow()}
        
        try:
            # Read Silver data
            silver_pv_df = self.spark.read.format("delta").load(f"{silver_path}/page_views")
            silver_sessions_df = self.spark.read.format("delta").load(f"{silver_path}/sessions")
            
            if date_str:
                silver_pv_df = silver_pv_df.filter(col("event_date") == date_str)
                silver_sessions_df = silver_sessions_df.filter(col("event_date") == date_str)
            
            # Calculate and write page metrics
            page_metrics_df = self.page_calculator.calculate_hourly_page_metrics(silver_pv_df)
            self.writer.write_page_metrics(page_metrics_df)
            stats["page_metrics_records"] = page_metrics_df.count()
            
            # Calculate session metrics
            session_metrics_df = self.session_calculator.calculate_session_metrics(
                silver_sessions_df
            )
            self.writer.write_session_metrics(session_metrics_df)
            stats["session_metrics_records"] = session_metrics_df.count()
            
            # Calculate user journey
            user_journey_df = self.user_calculator.calculate_user_metrics(
                silver_sessions_df, silver_pv_df
            )
            self.writer.write_user_journey(user_journey_df)
            stats["user_journey_records"] = user_journey_df.count()
            
            # Calculate funnel metrics (if configured)
            funnels_config = self.config.get("funnels", {})
            if funnels_config:
                funnel_metrics_df = self.funnel_calculator.calculate_funnel_conversion(
                    funnels_config, silver_sessions_df
                )
                self.writer.write_funnel_metrics(funnel_metrics_df)
                stats["funnel_metrics_records"] = funnel_metrics_df.count()
            
            # Calculate conversion metrics
            conversion_pages = self.config.get("conversion_pages", [])
            if conversion_pages:
                conversion_df = self.conversion_calculator.calculate_page_conversion(
                    silver_sessions_df, conversion_pages
                )
                self.writer.write_conversion(conversion_df)
                stats["conversion_records"] = conversion_df.count()
            
            stats["status"] = "success"
            
        except Exception as e:
            logger.error(f"Silver to Gold job failed: {e}", exc_info=True)
            stats["status"] = "failed"
            stats["error"] = str(e)
        
        finally:
            stats["end_time"] = datetime.utcnow()
        
        return stats
    
    def run_full_pipeline(self,
                         bronze_path: str,
                         silver_path: str,
                         gold_path: str,
                         date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Run full pipeline: Bronze -> Silver -> Gold.
        
        Args:
            bronze_path: Bronze input path
            silver_path: Silver intermediate path
            gold_path: Gold output path
            date_str: Date to process or None for latest
            
        Returns:
            Combined statistics from all jobs
        """
        logger.info("Starting full analytics pipeline")
        
        all_stats = {
            "start_time": datetime.utcnow(),
            "pipeline_stages": {}
        }
        
        # Bronze to Silver
        b2s_stats = self.run_bronze_to_silver_job(bronze_path, silver_path, date_str)
        all_stats["pipeline_stages"]["bronze_to_silver"] = b2s_stats
        
        if b2s_stats.get("status") == "failed":
            logger.error("Pipeline failed at Bronze to Silver stage")
            all_stats["status"] = "failed"
            return all_stats
        
        # Silver to Gold
        s2g_stats = self.run_silver_to_gold_job(silver_path, gold_path, date_str)
        all_stats["pipeline_stages"]["silver_to_gold"] = s2g_stats
        
        if s2g_stats.get("status") == "failed":
            logger.error("Pipeline failed at Silver to Gold stage")
            all_stats["status"] = "failed"
            return all_stats
        
        all_stats["status"] = "success"
        all_stats["end_time"] = datetime.utcnow()
        
        return all_stats
    
    def optimize_delta_tables(self, table_paths: List[str]) -> None:
        """
        Optimize Delta tables with VACUUM and ANALYZE.
        
        Args:
            table_paths: List of Delta table paths to optimize
        """
        logger.info(f"Optimizing {len(table_paths)} Delta tables")
        
        for path in table_paths:
            try:
                logger.info(f"Optimizing {path}")
                
                # VACUUM to remove old files
                self.spark.sql(f"VACUUM delta.`{path}` RETAIN 168 HOURS")
                
                # ANALYZE TABLE to update statistics
                self.spark.sql(f"ANALYZE TABLE delta.`{path}` COMPUTE STATISTICS")
                
                # Z-ORDER for common query patterns
                # This is example - should be configured per table
                self.spark.sql(f"OPTIMIZE delta.`{path}` ZORDER BY (event_date)")
                
                logger.info(f"Optimization complete for {path}")
            
            except Exception as e:
                logger.warning(f"Failed to optimize {path}: {e}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get current pipeline statistics"""
        return {
            "spark_version": self.spark.version,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Entry point for Airflow/Spark Job Cluster
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    import yaml
    
    load_dotenv()
    
    # Load configuration
    config_path = os.getenv("JOB_CONFIG_PATH", "/config/product_config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Create orchestrator
    orchestrator = SparkJobOrchestrator(config)
    
    # Run pipeline
    try:
        bronze_path = os.getenv("BRONZE_PATH", "/data/bronze")
        silver_path = os.getenv("SILVER_PATH", "/data/silver")
        gold_path = os.getenv("GOLD_PATH", "/data/gold")
        
        # Use current date if not specified
        date_str = os.getenv("PROCESS_DATE", 
                            (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"))
        
        stats = orchestrator.run_full_pipeline(bronze_path, silver_path, gold_path, date_str)
        
        logger.info(f"Pipeline complete: {stats}")
    
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
