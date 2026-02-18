"""
Metadata Manager - Centralized Metadata and Catalog Management

Provides:
- Data asset catalog
- Metadata versioning
- Data lineage tracking
- Tagging and classification
- Search and discovery
- Data quality metadata
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum


logger = logging.getLogger(__name__)


class AssetType(Enum):
    """Types of data assets"""
    DATASET = "dataset"
    TABLE = "table"
    VIEW = "view"
    DIMENSION = "dimension"
    FACT = "fact"
    DASHBOARD = "dashboard"
    REPORT = "report"
    QUERY = "query"
    METRIC = "metric"


class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class DataQualityMetrics:
    """Data quality metrics for an asset"""
    completeness: float = 100.0  # 0-100%
    accuracy: float = 100.0
    consistency: float = 100.0
    timeliness: float = 100.0
    validity: float = 100.0
    uniqueness: float = 100.0
    last_checked: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DataAsset:
    """Represents a data asset in the catalog"""
    id: str  # Unique asset ID
    name: str
    asset_type: AssetType
    description: str = ""
    owner: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_system: str = ""
    location: str = ""
    tags: List[str] = field(default_factory=list)
    classification: DataClassification = DataClassification.INTERNAL
    owner_email: str = ""
    support_contact: str = ""
    schema: Dict[str, str] = field(default_factory=dict)  # column -> type mappings
    lineage_upstream: List[str] = field(default_factory=list)  # Parent assets
    lineage_downstream: List[str] = field(default_factory=list)  # Dependent assets
    quality_metrics: DataQualityMetrics = field(default_factory=DataQualityMetrics)
    documentation_url: str = ""
    sla: Dict[str, Any] = field(default_factory=dict)  # Availability, latency, etc.
    refresh_frequency: str = ""  # daily, hourly, real-time, etc.
    record_count: int = 0
    size_bytes: int = 0
    last_modified: str = ""


class MetadataManager:
    """Manages data asset metadata and catalog"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Metadata Manager
        
        Args:
            config_path: Path to configuration file
        """
        from ..configs.bi_config import get_bi_config
        self.config = get_bi_config(config_path)
        self.storage_path = Path(self.config.get('metadata.storage', 'analytics_data/metadata'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.assets: Dict[str, DataAsset] = {}
        self.asset_index: Dict[str, Set[str]] = {}  # tag -> set of asset_ids
        self.lineage_graph: Dict[str, List[str]] = {}  # asset -> [dependent_assets]
        
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load existing metadata from storage"""
        catalog_file = self.storage_path / 'catalog.json'
        if catalog_file.exists():
            try:
                with open(catalog_file, 'r') as f:
                    data = json.load(f)
                    for asset_data in data.get('assets', []):
                        # Reconstruct enums
                        asset_data['asset_type'] = AssetType(asset_data.get('asset_type', 'dataset'))
                        asset_data['classification'] = DataClassification(
                            asset_data.get('classification', 'internal')
                        )
                        quality_data = asset_data.get('quality_metrics', {})
                        asset_data['quality_metrics'] = DataQualityMetrics(**quality_data)
                        
                        asset = DataAsset(**asset_data)
                        self.assets[asset.id] = asset
                        
                        # Rebuild index
                        for tag in asset.tags:
                            if tag not in self.asset_index:
                                self.asset_index[tag] = set()
                            self.asset_index[tag].add(asset.id)
                    
                    self.lineage_graph = data.get('lineage', {})
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save metadata to storage"""
        catalog_file = self.storage_path / 'catalog.json'
        data = {
            'version': self.config.get('version'),
            'timestamp': datetime.now().isoformat(),
            'assets': [
                {
                    **asdict(asset),
                    'asset_type': asset.asset_type.value,
                    'classification': asset.classification.value,
                    'quality_metrics': asdict(asset.quality_metrics)
                }
                for asset in self.assets.values()
            ],
            'lineage': self.lineage_graph
        }
        try:
            with open(catalog_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def register_asset(self, name: str, asset_type: AssetType,
                      description: str = "", owner: str = "",
                      source_system: str = "",
                      location: str = "") -> DataAsset:
        """Register a new data asset
        
        Args:
            name: Asset name
            asset_type: Type of asset
            description: Asset description
            owner: Asset owner
            source_system: Source system name
            location: Asset location/path
        
        Returns:
            Registered DataAsset
        """
        # Generate unique ID
        asset_id = f"{asset_type.value}_{name}_{datetime.now().timestamp()}"
        
        asset = DataAsset(
            id=asset_id,
            name=name,
            asset_type=asset_type,
            description=description,
            owner=owner,
            source_system=source_system,
            location=location
        )
        
        self.assets[asset_id] = asset
        logger.info(f"Registered asset: {name} ({asset_type.value})")
        self._save_metadata()
        
        return asset
    
    def add_tags(self, asset_id: str, tags: List[str]) -> DataAsset:
        """Add tags to an asset
        
        Args:
            asset_id: Asset ID
            tags: Tags to add
        
        Returns:
            Updated DataAsset
        """
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found")
        
        for tag in tags:
            if tag not in asset.tags:
                asset.tags.append(tag)
            
            # Update index
            if tag not in self.asset_index:
                self.asset_index[tag] = set()
            self.asset_index[tag].add(asset_id)
        
        asset.updated_at = datetime.now().isoformat()
        self._save_metadata()
        
        return asset
    
    def update_lineage(self, asset_id: str, upstream: List[str] = None, 
                      downstream: List[str] = None) -> DataAsset:
        """Update data lineage for an asset
        
        Args:
            asset_id: Asset ID
            upstream: List of upstream asset IDs
            downstream: List of downstream asset IDs
        
        Returns:
            Updated DataAsset
        """
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found")
        
        if upstream:
            asset.lineage_upstream = upstream
        
        if downstream:
            asset.lineage_downstream = downstream
            self.lineage_graph[asset_id] = downstream
        
        asset.updated_at = datetime.now().isoformat()
        self._save_metadata()
        
        return asset
    
    def update_quality_metrics(self, asset_id: str, 
                              metrics: DataQualityMetrics) -> DataAsset:
        """Update data quality metrics"""
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found")
        
        asset.quality_metrics = metrics
        asset.updated_at = datetime.now().isoformat()
        self._save_metadata()
        
        return asset
    
    def search_assets(self, query: str = "", asset_type: Optional[AssetType] = None,
                     classification: Optional[DataClassification] = None,
                     tags: Optional[List[str]] = None) -> List[DataAsset]:
        """Search for assets by various criteria
        
        Args:
            query: Search query (name or description)
            asset_type: Filter by asset type
            classification: Filter by classification
            tags: Filter by tags (assets with ANY of these tags)
        
        Returns:
            List of matching assets
        """
        results = list(self.assets.values())
        
        # Filter by query
        if query:
            query_lower = query.lower()
            results = [
                a for a in results
                if query_lower in a.name.lower() or
                   query_lower in a.description.lower()
            ]
        
        # Filter by type
        if asset_type:
            results = [a for a in results if a.asset_type == asset_type]
        
        # Filter by classification
        if classification:
            results = [a for a in results if a.classification == classification]
        
        # Filter by tags
        if tags:
            results = [
                a for a in results
                if any(tag in a.tags for tag in tags)
            ]
        
        return results
    
    def get_lineage_tree(self, asset_id: str, direction: str = "both") -> Dict[str, Any]:
        """Get complete lineage tree for an asset
        
        Args:
            asset_id: Asset ID
            direction: 'upstream', 'downstream', or 'both'
        
        Returns:
            Lineage tree structure
        """
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found")
        
        tree = {
            'asset': asset.name,
            'id': asset_id,
            'type': asset.asset_type.value,
            'upstream': [],
            'downstream': []
        }
        
        if direction in ['upstream', 'both']:
            for upstream_id in asset.lineage_upstream:
                upstream_asset = self.assets.get(upstream_id)
                if upstream_asset:
                    tree['upstream'].append({
                        'asset': upstream_asset.name,
                        'id': upstream_id,
                        'type': upstream_asset.asset_type.value
                    })
        
        if direction in ['downstream', 'both']:
            for downstream_id in asset.lineage_downstream:
                downstream_asset = self.assets.get(downstream_id)
                if downstream_asset:
                    tree['downstream'].append({
                        'asset': downstream_asset.name,
                        'id': downstream_id,
                        'type': downstream_asset.asset_type.value
                    })
        
        return tree
    
    def get_asset(self, asset_id: str) -> Optional[DataAsset]:
        """Get asset by ID"""
        return self.assets.get(asset_id)
    
    def list_assets_by_tag(self, tag: str) -> List[DataAsset]:
        """List all assets with a specific tag"""
        asset_ids = self.asset_index.get(tag, set())
        return [self.assets[aid] for aid in asset_ids if aid in self.assets]
    
    def get_impact_analysis(self, asset_id: str) -> Dict[str, Any]:
        """Get impact analysis for an asset
        
        Args:
            asset_id: Asset ID
        
        Returns:
            Impact analysis showing dependent assets
        """
        asset = self.assets.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found")
        
        # Recursively traverse downstream
        def get_all_downstream(aid, visited=None):
            if visited is None:
                visited = set()
            if aid in visited:
                return []
            visited.add(aid)
            
            downstream = []
            for dep_id in self.lineage_graph.get(aid, []):
                downstream.append(dep_id)
                downstream.extend(get_all_downstream(dep_id, visited))
            return downstream
        
        all_downstream = get_all_downstream(asset_id)
        
        return {
            'asset': asset.name,
            'id': asset_id,
            'direct_dependencies': asset.lineage_downstream,
            'all_dependencies': list(set(all_downstream)),
            'dependency_count': len(set(all_downstream)),
            'high_risk': len(set(all_downstream)) > 10
        }
    
    def get_catalog_summary(self) -> Dict[str, Any]:
        """Get catalog summary statistics"""
        by_type = {}
        by_classification = {}
        by_owner = {}
        
        for asset in self.assets.values():
            # Count by type
            type_key = asset.asset_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # Count by classification
            class_key = asset.classification.value
            by_classification[class_key] = by_classification.get(class_key, 0) + 1
            
            # Count by owner
            owner_key = asset.owner or "Unassigned"
            by_owner[owner_key] = by_owner.get(owner_key, 0) + 1
        
        return {
            'total_assets': len(self.assets),
            'by_type': by_type,
            'by_classification': by_classification,
            'by_owner': by_owner,
            'total_tags': len(self.asset_index),
            'timestamp': datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of metadata manager"""
        return {
            'status': 'healthy',
            'assets_count': len(self.assets),
            'tags_count': len(self.asset_index),
            'storage_path': str(self.storage_path),
            'timestamp': datetime.now().isoformat()
        }


def get_metadata_manager(config_path: Optional[str] = None) -> MetadataManager:
    """Factory function to get MetadataManager instance"""
    return MetadataManager(config_path)
