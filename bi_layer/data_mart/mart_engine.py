"""
Data Mart Engine

Provides dimensional modeling and fact table management for analytical queries.
Implements the Kimball approach to dimensional modeling with support for:
- Dimension tables (slowly changing dimensions)
- Fact tables (measures)
- Conformed dimensions
- Data mart schemas
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


@dataclass
class Dimension:
    """Represents a dimension table in the data mart"""
    name: str
    columns: List[Dict[str, str]]  # [{'name': 'col', 'type': 'int', 'key': True}]
    table_name: str
    description: str = ""
    scd_type: int = 1  # Type 1, 2, or 3 (Slowly Changing Dimension)
    grain: str = ""  # Business grain of the dimension


@dataclass
class Fact:
    """Represents a fact table in the data mart"""
    name: str
    columns: List[Dict[str, str]]  # Columns including measures and foreign keys
    table_name: str
    grain: str  # Fact grain (e.g., "transaction", "daily", "hourly")
    description: str = ""
    fact_type: str = "transaction"  # transaction or cumulative


class DataMartEngine:
    """Manages data marts with dimensional modeling"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Data Mart engine
        
        Args:
            config_path: Path to configuration file
        """
        from ..configs.bi_config import get_bi_config
        self.config = get_bi_config(config_path)
        self.storage_path = Path(self.config.get('data_mart.storage'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.dimensions: Dict[str, Dimension] = {}
        self.facts: Dict[str, Fact] = {}
        self.marts: Dict[str, Dict] = {}
        
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load existing data mart metadata"""
        metadata_file = self.storage_path / 'metadata.json'
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    
                    for dim_data in data.get('dimensions', []):
                        dim = Dimension(**dim_data)
                        self.dimensions[dim.name] = dim
                    
                    for fact_data in data.get('facts', []):
                        fact = Fact(**fact_data)
                        self.facts[fact.name] = fact
                    
                    self.marts = data.get('marts', {})
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save data mart metadata"""
        metadata_file = self.storage_path / 'metadata.json'
        data = {
            'version': self.config.get('version'),
            'timestamp': datetime.now().isoformat(),
            'dimensions': [asdict(dim) for dim in self.dimensions.values()],
            'facts': [asdict(fact) for fact in self.facts.values()],
            'marts': self.marts
        }
        try:
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def create_dimension(self, name: str, columns: List[Dict], 
                        table_name: str, description: str = "",
                        scd_type: int = 1, grain: str = "") -> Dimension:
        """Create a new dimension
        
        Args:
            name: Dimension name
            columns: List of column definitions
            table_name: Table name in data warehouse
            description: Dimension description
            scd_type: Slowly Changing Dimension type (1, 2, or 3)
            grain: Business grain of the dimension
        
        Returns:
            Created Dimension object
        """
        dimension = Dimension(
            name=name,
            columns=columns,
            table_name=table_name,
            description=description,
            scd_type=scd_type,
            grain=grain
        )
        self.dimensions[name] = dimension
        
        # Log dimension creation
        logger.info(f"Created dimension: {name} (table: {table_name})")
        
        # Save metadata
        self._save_metadata()
        
        return dimension
    
    def create_fact(self, name: str, columns: List[Dict],
                   table_name: str, grain: str,
                   description: str = "",
                   fact_type: str = "transaction") -> Fact:
        """Create a new fact table
        
        Args:
            name: Fact table name
            columns: List of column definitions (measures and foreign keys)
            table_name: Table name in data warehouse
            grain: Fact grain (e.g., "transaction", "daily")
            description: Fact table description
            fact_type: Type of fact (transaction or cumulative)
        
        Returns:
            Created Fact object
        """
        fact = Fact(
            name=name,
            columns=columns,
            table_name=table_name,
            grain=grain,
            description=description,
            fact_type=fact_type
        )
        self.facts[name] = fact
        
        logger.info(f"Created fact table: {name} (grain: {grain})")
        self._save_metadata()
        
        return fact
    
    def create_data_mart(self, mart_name: str, 
                        dimensions: List[str],
                        facts: List[str],
                        description: str = "") -> Dict:
        """Create a data mart schema by combining dimensions and facts
        
        Args:
            mart_name: Name of the data mart
            dimensions: List of dimension names
            facts: List of fact names
            description: Data mart description
        
        Returns:
            Data mart configuration dictionary
        """
        # Validate that all dimensions and facts exist
        for dim_name in dimensions:
            if dim_name not in self.dimensions:
                raise ValueError(f"Dimension '{dim_name}' not found")
        
        for fact_name in facts:
            if fact_name not in self.facts:
                raise ValueError(f"Fact table '{fact_name}' not found")
        
        mart_config = {
            'name': mart_name,
            'dimensions': dimensions,
            'facts': facts,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'schema_type': 'star'  # Star schema
        }
        
        self.marts[mart_name] = mart_config
        
        logger.info(f"Created data mart: {mart_name}")
        self._save_metadata()
        
        return mart_config
    
    def get_dimension(self, name: str) -> Optional[Dimension]:
        """Get dimension by name
        
        Args:
            name: Dimension name
        
        Returns:
            Dimension object or None if not found
        """
        return self.dimensions.get(name)
    
    def get_fact(self, name: str) -> Optional[Fact]:
        """Get fact table by name
        
        Args:
            name: Fact table name
        
        Returns:
            Fact object or None if not found
        """
        return self.facts.get(name)
    
    def get_data_mart(self, mart_name: str) -> Optional[Dict]:
        """Get data mart configuration
        
        Args:
            mart_name: Data mart name
        
        Returns:
            Data mart configuration or None if not found
        """
        return self.marts.get(mart_name)
    
    def list_dimensions(self) -> List[str]:
        """List all dimension names
        
        Returns:
            List of dimension names
        """
        return list(self.dimensions.keys())
    
    def list_facts(self) -> List[str]:
        """List all fact table names
        
        Returns:
            List of fact table names
        """
        return list(self.facts.keys())
    
    def list_data_marts(self) -> List[str]:
        """List all data marts
        
        Returns:
            List of data mart names
        """
        return list(self.marts.keys())
    
    def get_mart_schema(self, mart_name: str) -> Dict:
        """Get complete schema for a data mart
        
        Args:
            mart_name: Data mart name
        
        Returns:
            Complete schema with all dimensions and facts
        """
        mart = self.get_data_mart(mart_name)
        if not mart:
            raise ValueError(f"Data mart '{mart_name}' not found")
        
        schema = {
            'name': mart['name'],
            'description': mart['description'],
            'dimensions': {},
            'facts': {}
        }
        
        for dim_name in mart['dimensions']:
            dim = self.get_dimension(dim_name)
            if dim:
                schema['dimensions'][dim_name] = asdict(dim)
        
        for fact_name in mart['facts']:
            fact = self.get_fact(fact_name)
            if fact:
                schema['facts'][fact_name] = asdict(fact)
        
        return schema
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of data mart engine
        
        Returns:
            Health status
        """
        return {
            'status': 'healthy',
            'dimensions_count': len(self.dimensions),
            'facts_count': len(self.facts),
            'marts_count': len(self.marts),
            'storage_path': str(self.storage_path),
            'timestamp': datetime.now().isoformat()
        }

def get_data_mart_engine(config_path: Optional[str] = None) -> DataMartEngine:
    """Factory function to get DataMartEngine instance
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        DataMartEngine instance
    """
    return DataMartEngine(config_path)