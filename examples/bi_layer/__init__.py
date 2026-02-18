"""
BI Layer - Business Intelligence and Analytics Module

Provides comprehensive BI capabilities including:
- Data Mart Management (dimensional modeling)
- Dashboard Builder
- Report Generator
- Metadata Management
- Query Optimization
- Visualization Components
- REST API
"""

from .data_mart.mart_engine import DataMartEngine
from .dashboard.dashboard_builder import DashboardBuilder
from .reports.report_generator import ReportGenerator
from .metadata.metadata_manager import MetadataManager
from .query_engine.query_optimizer import QueryOptimizer
from .visualization.chart_factory import ChartFactory

__version__ = "1.0.0"
__all__ = [
    "DataMartEngine",
    "DashboardBuilder",
    "ReportGenerator",
    "MetadataManager",
    "QueryOptimizer",
    "ChartFactory"
]


class BILayerManager:
    """Central manager for all BI layer operations"""
    
    def __init__(self, config_path=None):
        """Initialize BI Layer manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.data_mart = DataMartEngine(config_path)
        self.dashboard = DashboardBuilder(config_path)
        self.reports = ReportGenerator(config_path)
        self.metadata = MetadataManager(config_path)
        self.query_engine = QueryOptimizer(config_path)
        self.visualization = ChartFactory(config_path)
    
    def get_component(self, name):
        """Get a specific BI component
        
        Args:
            name: Component name (data_mart, dashboard, reports, metadata, query_engine, visualization)
        
        Returns:
            The requested component
        """
        components = {
            'data_mart': self.data_mart,
            'dashboard': self.dashboard,
            'reports': self.reports,
            'metadata': self.metadata,
            'query_engine': self.query_engine,
            'visualization': self.visualization
        }
        return components.get(name)
    
    def health_check(self):
        """Check health status of all BI components
        
        Returns:
            dict: Health status of each component
        """
        return {
            'data_mart': self.data_mart.health_check(),
            'dashboard': self.dashboard.health_check(),
            'reports': self.reports.health_check(),
            'metadata': self.metadata.health_check(),
            'query_engine': self.query_engine.health_check(),
            'visualization': self.visualization.health_check()
        }


# Global instance
_bi_manager = None


def get_bi_manager(config_path=None):
    """Get the global BI manager instance
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        BILayerManager: Global BI manager instance
    """
    global _bi_manager
    if _bi_manager is None:
        _bi_manager = BILayerManager(config_path)
    return _bi_manager
