"""
Data Catalog and Metadata Manager
Maintains table metadata, lineage, and data governance information
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from configs.logging_config import setup_logging


logger = setup_logging(__name__)


@dataclass
class TableMetadata:
    """Metadata for a lakehouse table"""
    table_name: str
    layer: str  # bronze, silver, gold
    path: str
    created_timestamp: str
    last_updated_timestamp: str
    owner: str = 'lakehouse'
    description: str = ''
    record_count: int = 0
    size_bytes: int = 0
    schema_version: int = 1
    retention_days: int = 365
    partitions: List[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.partitions is None:
            self.partitions = []
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class DataLineage:
    """Data lineage tracking"""
    source_table: str
    target_table: str
    transformation_job: str
    timestamp: str
    operation_type: str  # transform, aggregate, load
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class DataCatalog:
    """Data catalog for managing lakehouse metadata"""
    
    def __init__(self, catalog_path: str = '/var/lib/lakehouse/catalog'):
        self.catalog_path = Path(catalog_path)
        self.catalog_path.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.catalog_path / 'metadata.json'
        self.lineage_file = self.catalog_path / 'lineage.json'
        
        self.logger = logger
        self._load_catalog()
    
    def _load_catalog(self) -> None:
        """Load existing catalog from disk"""
        self.tables = {}
        self.lineage = []
        
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.tables = {
                        k: TableMetadata(**v) for k, v in data.items()
                    }
                self.logger.info(f"✅ Loaded {len(self.tables)} table metadata entries")
            except Exception as e:
                self.logger.warning(f"Failed to load metadata: {e}")
        
        if self.lineage_file.exists():
            try:
                with open(self.lineage_file, 'r') as f:
                    data = json.load(f)
                    self.lineage = [DataLineage(**item) for item in data]
                self.logger.info(f"✅ Loaded {len(self.lineage)} lineage entries")
            except Exception as e:
                self.logger.warning(f"Failed to load lineage: {e}")
    
    def _save_catalog(self) -> None:
        """Save catalog to disk"""
        # Save metadata
        with open(self.metadata_file, 'w') as f:
            data = {k: v.to_dict() for k, v in self.tables.items()}
            json.dump(data, f, indent=2)
        
        # Save lineage
        with open(self.lineage_file, 'w') as f:
            data = [item.to_dict() for item in self.lineage]
            json.dump(data, f, indent=2)
    
    def register_table(
        self,
        table_name: str,
        layer: str,
        path: str,
        owner: str = 'lakehouse',
        description: str = '',
        retention_days: int = 365,
        partitions: List[str] = None,
        tags: List[str] = None,
    ) -> TableMetadata:
        """
        Register a table in the catalog
        
        Args:
            table_name: Table name
            layer: Lakehouse layer (bronze, silver, gold)
            path: Path to table data
            owner: Table owner
            description: Table description
            retention_days: Data retention period
            partitions: Partition columns
            tags: Table tags for organization
        
        Returns:
            TableMetadata object
        """
        metadata = TableMetadata(
            table_name=table_name,
            layer=layer,
            path=path,
            created_timestamp=datetime.utcnow().isoformat(),
            last_updated_timestamp=datetime.utcnow().isoformat(),
            owner=owner,
            description=description,
            retention_days=retention_days,
            partitions=partitions or [],
            tags=tags or [],
        )
        
        self.tables[table_name] = metadata
        self._save_catalog()
        
        self.logger.info(f"📋 Registered table: {table_name} ({layer})")
        return metadata
    
    def update_table_stats(
        self,
        table_name: str,
        record_count: int,
        size_bytes: int,
    ) -> None:
        """Update table statistics"""
        if table_name in self.tables:
            self.tables[table_name].record_count = record_count
            self.tables[table_name].size_bytes = size_bytes
            self.tables[table_name].last_updated_timestamp = datetime.utcnow().isoformat()
            self._save_catalog()
            
            self.logger.info(
                f"📊 Updated stats for {table_name}: "
                f"{record_count} records, {size_bytes} bytes"
            )
    
    def track_lineage(
        self,
        source_table: str,
        target_table: str,
        transformation_job: str,
        operation_type: str = 'transform',
    ) -> DataLineage:
        """
        Track data lineage between tables
        
        Args:
            source_table: Source table name
            target_table: Target table name
            transformation_job: Job that performed transformation
            operation_type: Type of operation (transform, aggregate, load)
        
        Returns:
            DataLineage object
        """
        lineage = DataLineage(
            source_table=source_table,
            target_table=target_table,
            transformation_job=transformation_job,
            timestamp=datetime.utcnow().isoformat(),
            operation_type=operation_type,
        )
        
        self.lineage.append(lineage)
        self._save_catalog()
        
        self.logger.info(
            f"🔗 Tracked lineage: {source_table} → {target_table} "
            f"(via {transformation_job})"
        )
        return lineage
    
    def get_table_metadata(self, table_name: str) -> Optional[TableMetadata]:
        """Get metadata for a specific table"""
        return self.tables.get(table_name)
    
    def get_layer_tables(self, layer: str) -> List[TableMetadata]:
        """Get all tables in a specific layer"""
        return [t for t in self.tables.values() if t.layer == layer]
    
    def get_table_lineage(self, table_name: str) -> Dict[str, List[str]]:
        """Get lineage (upstream and downstream) for a table"""
        upstream = [
            item.source_table for item in self.lineage
            if item.target_table == table_name
        ]
        downstream = [
            item.target_table for item in self.lineage
            if item.source_table == table_name
        ]
        
        return {
            'upstream': list(set(upstream)),
            'downstream': list(set(downstream)),
        }
    
    def export_catalog(self, export_path: str) -> None:
        """Export catalog to file"""
        with open(export_path, 'w') as f:
            catalog_data = {
                'exported_timestamp': datetime.utcnow().isoformat(),
                'tables': {k: v.to_dict() for k, v in self.tables.items()},
                'lineage': [item.to_dict() for item in self.lineage],
            }
            json.dump(catalog_data, f, indent=2)
        
        self.logger.info(f"📤 Exported catalog to {export_path}")
    
    def get_catalog_report(self) -> Dict[str, Any]:
        """Generate catalog report"""
        bronze_tables = self.get_layer_tables('bronze')
        silver_tables = self.get_layer_tables('silver')
        gold_tables = self.get_layer_tables('gold')
        
        return {
            'report_timestamp': datetime.utcnow().isoformat(),
            'total_tables': len(self.tables),
            'by_layer': {
                'bronze': len(bronze_tables),
                'silver': len(silver_tables),
                'gold': len(gold_tables),
            },
            'total_records': sum(t.record_count for t in self.tables.values()),
            'total_size_gb': sum(t.size_bytes for t in self.tables.values()) / (1024**3),
            'lineage_entries': len(self.lineage),
        }


# Global catalog instance
_catalog = None


def get_catalog() -> DataCatalog:
    """Get global catalog instance"""
    global _catalog
    if _catalog is None:
        _catalog = DataCatalog()
    return _catalog
