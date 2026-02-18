"""
BI Layer Configuration Management

Handles configuration for all BI components including:
- Data Mart settings
- Dashboard configurations
- Report generation settings
- Metadata store configuration
- Query optimization parameters
- Visualization settings
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class BIConfig:
    """Central configuration manager for BI Layer"""
    
    # Default configuration
    DEFAULT_CONFIG = {
        'version': '1.0',
        'environment': os.getenv('BI_ENV', 'development'),
        'debug': os.getenv('BI_DEBUG', 'True').lower() == 'true',
        
        # Data Mart Configuration
        'data_mart': {
            'type': 'dimension_fact',
            'storage': os.getenv('BI_DATA_MART_PATH', '/workspaces/Data-Platform/bi_data/marts'),
            'cache_enabled': True,
            'cache_ttl_seconds': 3600,
            'partitioning': {
                'enabled': True,
                'columns': ['date_key', 'year', 'month']
            },
            'indexing': {
                'enabled': True,
                'columns': ['product_id', 'customer_id', 'time_key']
            }
        },
        
        # Dashboard Configuration
        'dashboard': {
            'storage': os.getenv('BI_DASHBOARD_PATH', '/workspaces/Data-Platform/bi_data/dashboards'),
            'max_dashboards': 1000,
            'refresh_interval': 300,  # 5 minutes default
            'grid_size': 12,
            'export_formats': ['json', 'pdf', 'html'],
            'theme': 'light'
        },
        
        # Report Configuration
        'reports': {
            'storage': os.getenv('BI_REPORTS_PATH', '/workspaces/Data-Platform/bi_data/reports'),
            'formats': ['pdf', 'excel', 'html', 'csv'],
            'schedule_enabled': True,
            'max_report_size_mb': 500,
            'font': 'Arial',
            'page_size': 'A4'
        },
        
        # Metadata Configuration
        'metadata': {
            'store': os.getenv('BI_METADATA_STORE', 'json'),  # json, sqlite, postgresql
            'storage': os.getenv('BI_METADATA_PATH', '/workspaces/Data-Platform/bi_data/metadata'),
            'enable_lineage': True,
            'enable_tagging': True,
            'versioning': True
        },
        
        # Query Engine Configuration
        'query_engine': {
            'engine': 'duckdb',  # duckdb, presto, spark
            'connection': {
                'type': 'local',
                'timeout_seconds': 300
            },
            'optimization': {
                'enabled': True,
                'cache_queries': True,
                'query_cache_size_mb': 500
            },
            'limits': {
                'max_rows': 1000000,
                'max_query_time_seconds': 3600,
                'result_cache_ttl': 3600
            }
        },
        
        # Visualization Configuration
        'visualization': {
            'library': 'plotly',  # plotly, matplotlib, altair
            'default_chart_type': 'bar',
            'theme': 'plotly_white',
            'export_formats': ['html', 'png', 'svg'],
            'max_chart_data_points': 100000
        },
        
        # API Configuration
        'api': {
            'host': os.getenv('BI_API_HOST', '0.0.0.0'),
            'port': int(os.getenv('BI_API_PORT', '8900')),
            'debug': os.getenv('BI_API_DEBUG', 'True').lower() == 'true',
            'enable_cors': True,
            'request_timeout': 300,
            'max_request_size_mb': 100
        },
        
        # Logging Configuration
        'logging': {
            'level': os.getenv('BI_LOG_LEVEL', 'INFO'),
            'file': os.getenv('BI_LOG_FILE', '/workspaces/Data-Platform/bi_layer/logs/bi_layer.log'),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration
        
        Args:
            config_path: Path to configuration file (JSON)
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path and Path(config_path).exists():
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> None:
        """Load configuration from JSON file
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                self._deep_update(self.config, user_config)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
    
    def _deep_update(self, base: Dict, update: Dict) -> None:
        """Deep merge update dict into base dict
        
        Args:
            base: Base configuration dictionary
            update: Update configuration dictionary
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value
        
        Args:
            key: Configuration key (dot notation supported)
            value: Configuration value
        """
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict:
        """Get configuration as dictionary
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
    
    def save_config(self, output_path: str) -> None:
        """Save configuration to JSON file
        
        Args:
            output_path: Path to save configuration
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def validate(self) -> Dict[str, bool]:
        """Validate configuration
        
        Returns:
            Validation results
        """
        validation = {
            'data_mart_path': Path(self.get('data_mart.storage')).exists(),
            'dashboard_path': Path(self.get('dashboard.storage')).exists(),
            'reports_path': Path(self.get('reports.storage')).exists(),
            'metadata_path': Path(self.get('metadata.storage')).exists(),
        }
        return validation


# Global configuration instance
_config = None


def get_bi_config(config_path: Optional[str] = None) -> BIConfig:
    """Get or create global configuration instance
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        BIConfig: Global configuration instance
    """
    global _config
    if _config is None:
        _config = BIConfig(config_path)
    return _config
