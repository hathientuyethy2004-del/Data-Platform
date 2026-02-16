"""
Lakehouse Monitoring and Health Checks
Monitors lakehouse health, table quality, and performance metrics
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from configs.lakehouse_config import lakehouse_config
from configs.logging_config import setup_logging, LogContext
from utils.delta_utils import DeltaLakeManager
from utils.quality_checks import DataQualityChecker
from catalog.data_catalog import get_catalog


logger = setup_logging(__name__, lakehouse_config.log_level)


class LakehouseHealthMonitor:
    """Monitors lakehouse health and generates health reports"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.config = lakehouse_config
        self.delta_manager = DeltaLakeManager(spark)
        self.quality_checker = DataQualityChecker()
        self.catalog = get_catalog()
        self.logger = logger
        self.health_checks = []
    
    def check_table_health(self, table_name: str, layer: str) -> Dict[str, Any]:
        """Check health of a specific table"""
        operation = f"check_health_{layer}_{table_name}"
        
        with LogContext(self.logger, operation):
            try:
                # Get metadata
                metadata = self.catalog.get_table_metadata(table_name)
                if not metadata:
                    return {
                        'table': table_name,
                        'layer': layer,
                        'status': 'not_found',
                    }
                
                # Read table
                df = self.delta_manager.read_delta_table(table_name, layer)
                record_count = df.count()
                
                # Check age
                table_path = getattr(self.config, f'{layer}_path') + f'/{table_name}'
                
                try:
                    history = self.spark.sql(f"DESCRIBE HISTORY delta.`{table_path}`")
                    last_update = history.collect()[0]['timestamp']
                except:
                    last_update = None
                
                # Data quality checks
                null_check = self.quality_checker.check_null_values(
                    df,
                    df.columns[0],  # Check first column
                    threshold_percent=10.0
                )
                
                health_status = {
                    'table': table_name,
                    'layer': layer,
                    'status': 'healthy',
                    'record_count': record_count,
                    'column_count': len(df.columns),
                    'last_updated': last_update,
                    'data_quality': null_check['passed'],
                    'checks_passed': 1 if null_check['passed'] else 0,
                    'timestamp': datetime.utcnow().isoformat(),
                }
                
                self.health_checks.append(health_status)
                return health_status
            
            except Exception as e:
                self.logger.error(f"Health check failed for {table_name}: {e}")
                return {
                    'table': table_name,
                    'layer': layer,
                    'status': 'unhealthy',
                    'error': str(e),
                }
    
    def check_bronze_health(self) -> Dict[str, Any]:
        """Check Bronze layer health"""
        with LogContext(self.logger, "check_bronze_health"):
            results = []
            bronze_tables = self.catalog.get_layer_tables('bronze')
            
            for table in bronze_tables:
                results.append(self.check_table_health(table.table_name, 'bronze'))
            
            return {
                'layer': 'bronze',
                'tables_checked': len(results),
                'tables': results,
                'healthy_count': sum(1 for r in results if r.get('status') == 'healthy'),
            }
    
    def check_silver_health(self) -> Dict[str, Any]:
        """Check Silver layer health"""
        with LogContext(self.logger, "check_silver_health"):
            results = []
            silver_tables = self.catalog.get_layer_tables('silver')
            
            for table in silver_tables:
                results.append(self.check_table_health(table.table_name, 'silver'))
            
            return {
                'layer': 'silver',
                'tables_checked': len(results),
                'tables': results,
                'healthy_count': sum(1 for r in results if r.get('status') == 'healthy'),
            }
    
    def check_gold_health(self) -> Dict[str, Any]:
        """Check Gold layer health"""
        with LogContext(self.logger, "check_gold_health"):
            results = []
            gold_tables = self.catalog.get_layer_tables('gold')
            
            for table in gold_tables:
                results.append(self.check_table_health(table.table_name, 'gold'))
            
            return {
                'layer': 'gold',
                'tables_checked': len(results),
                'tables': results,
                'healthy_count': sum(1 for r in results if r.get('status') == 'healthy'),
            }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        with LogContext(self.logger, "get_storage_stats"):
            total_size = 0
            table_count = 0
            record_count = 0
            
            for table in self.catalog.tables.values():
                total_size += table.size_bytes
                table_count += 1
                record_count += table.record_count
            
            return {
                'total_tables': table_count,
                'total_records': record_count,
                'total_size_gb': round(total_size / (1024**3), 2),
                'avg_table_size_mb': round((total_size / table_count) / (1024**2), 2) if table_count > 0 else 0,
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with LogContext(self.logger, "get_performance_stats"):
            # Calculate approximate processing metrics
            return {
                'spark_version': self.spark.version,
                'total_executor_cores': self.spark.sparkContext.defaultParallelism,
                'driver_memory': 'unknown',
                'executor_memory': 'unknown',
            }
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        self.logger.info("=" * 80)
        self.logger.info("🏥 LAKEHOUSE HEALTH REPORT")
        self.logger.info("=" * 80)
        
        bronze_health = self.check_bronze_health()
        silver_health = self.check_silver_health()
        gold_health = self.check_gold_health()
        storage_stats = self.get_storage_stats()
        performance_stats = self.get_performance_stats()
        
        # Overall status
        unhealthy_count = sum(
            1 for checks in [bronze_health, silver_health, gold_health]
            for table in checks.get('tables', [])
            if table.get('status') != 'healthy'
        )
        
        overall_status = 'healthy' if unhealthy_count == 0 else 'degraded'
        
        report = {
            'report_timestamp': datetime.utcnow().isoformat(),
            'overall_status': overall_status,
            'layers': {
                'bronze': bronze_health,
                'silver': silver_health,
                'gold': gold_health,
            },
            'storage': storage_stats,
            'performance': performance_stats,
            'statistics': {
                'total_health_checks': len(self.health_checks),
                'unhealthy_tables': unhealthy_count,
            },
        }
        
        # Log summary
        self.logger.info(f"Status: {overall_status.upper()}")
        self.logger.info(f"Bronze: {bronze_health['healthy_count']}/{bronze_health['tables_checked']} healthy")
        self.logger.info(f"Silver: {silver_health['healthy_count']}/{silver_health['tables_checked']} healthy")
        self.logger.info(f"Gold: {gold_health['healthy_count']}/{gold_health['tables_checked']} healthy")
        self.logger.info(f"Storage: {storage_stats['total_size_gb']} GB across {storage_stats['total_tables']} tables")
        self.logger.info("=" * 80)
        
        return report
    
    def save_report(self, output_path: str = None) -> None:
        """Save health report to file"""
        if output_path is None:
            output_path = f"{self.config.logs_dir}/health_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.generate_health_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📊 Health report saved to: {output_path}")


def create_spark_session() -> SparkSession:
    """Create Spark session"""
    return SparkSession.builder \
        .appName('lakehouse-monitoring') \
        .master(lakehouse_config.spark_master) \
        .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension') \
        .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog') \
        .getOrCreate()


if __name__ == '__main__':
    spark = create_spark_session()
    
    try:
        monitor = LakehouseHealthMonitor(spark)
        monitor.save_report()
        
    except Exception as e:
        logger.error(f"Monitoring failed: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        spark.stop()
