"""
Data Catalog System
Central metadata repository for all data assets with classification, ownership, and versioning
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from config.governance_config import DataClassification, governance_config


class AssetType(Enum):
    """Data asset types"""
    TABLE = "table"
    VIEW = "view"
    DATASET = "dataset"
    REPORT = "report"
    METRIC = "metric"
    DASHBOARD = "dashboard"


@dataclass
class ColumnMetadata:
    """Column metadata"""
    name: str
    data_type: str
    nullable: bool = True
    description: str = ""
    classification: str = DataClassification.INTERNAL.value
    pii_type: Optional[str] = None  # email, phone, ssn, credit_card, etc.
    is_sensitive: bool = False
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
            self.updated_at = self.created_at


@dataclass
class DataAssetMetadata:
    """Data asset metadata"""
    asset_id: str
    asset_name: str
    asset_type: str
    layer: str  # bronze, silver, gold
    platform: str  # parquet, postgres, etc.
    location: str  # Full path or connection string
    
    # Meta information
    owner: str
    owner_email: str
    owner_team: str
    description: str = ""
    tags: List[str] = None
    
    # Classification & sensitivity
    classification: str = DataClassification.INTERNAL.value
    contains_pii: bool = False
    pii_columns: List[str] = None
    
    # Technical details
    record_count: int = 0
    size_bytes: int = 0
    columns: List[ColumnMetadata] = None
    schema_version: str = "1.0"
    
    # Compliance
    compliance_frameworks: List[str] = None
    retention_days: int = 365
    gdpr_applicable: bool = False
    ccpa_applicable: bool = False
    
    # Freshness & SLA
    last_updated: str = ""
    expected_update_frequency: str = "daily"  # hourly, daily, weekly, monthly, on-demand
    sla_freshness_hours: int = 24
    sla_completeness_percent: float = 95.0
    
    # Quality
    quality_score: float = 100.0
    last_quality_check: str = ""
    
    # Lineage references
    source_assets: List[str] = None
    dependent_assets: List[str] = None
    
    # Metadata
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    version: int = 1
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
            self.updated_at = self.created_at
        if self.tags is None:
            self.tags = []
        if self.pii_columns is None:
            self.pii_columns = []
        if self.columns is None:
            self.columns = []
        if self.compliance_frameworks is None:
            self.compliance_frameworks = []
        if self.source_assets is None:
            self.source_assets = []
        if self.dependent_assets is None:
            self.dependent_assets = []


class DataCatalog:
    """Central data catalog system"""

    def __init__(self):
        """Initialize data catalog"""
        self.storage_path = Path(governance_config.catalog.catalog_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.assets_file = self.storage_path / "assets.json"
        self.columns_file = self.storage_path / "columns.json"
        self.tags_index_file = self.storage_path / "tags_index.json"
        self.owners_index_file = self.storage_path / "owners_index.json"
        
        self.assets: Dict[str, DataAssetMetadata] = self._load_assets()
        self.tags_index: Dict[str, List[str]] = self._load_tags_index()
        self.owners_index: Dict[str, List[str]] = self._load_owners_index()

    def register_asset(self, asset: DataAssetMetadata) -> str:
        """Register a new data asset"""
        # Generate asset ID if not provided
        if not asset.asset_id:
            asset.asset_id = str(uuid.uuid4())
        
        asset.created_at = datetime.now().isoformat()
        asset.updated_at = asset.created_at
        
        self.assets[asset.asset_id] = asset
        
        # Update indices
        self._update_tag_index(asset.asset_id, asset.tags)
        self._update_owner_index(asset.asset_id, asset.owner)
        
        self._save_assets()
        return asset.asset_id

    def get_asset(self, asset_id: str) -> Optional[DataAssetMetadata]:
        """Get asset metadata by ID"""
        return self.assets.get(asset_id)

    def get_asset_by_name(self, asset_name: str) -> Optional[DataAssetMetadata]:
        """Get asset metadata by name"""
        for asset in self.assets.values():
            if asset.asset_name == asset_name:
                return asset
        return None

    def get_assets_by_layer(self, layer: str) -> List[DataAssetMetadata]:
        """Get all assets in a layer"""
        return [a for a in self.assets.values() if a.layer == layer]

    def get_assets_by_owner(self, owner: str) -> List[DataAssetMetadata]:
        """Get all assets owned by a person/team"""
        return [a for a in self.assets.values() if a.owner == owner]

    def get_assets_by_tag(self, tag: str) -> List[DataAssetMetadata]:
        """Get all assets with a specific tag"""
        asset_ids = self.tags_index.get(tag, [])
        return [self.assets[aid] for aid in asset_ids if aid in self.assets]

    def get_assets_by_classification(self, classification: str) -> List[DataAssetMetadata]:
        """Get all assets with a classification"""
        return [a for a in self.assets.values() if a.classification == classification]

    def get_pii_assets(self) -> List[DataAssetMetadata]:
        """Get all assets containing PII"""
        return [a for a in self.assets.values() if a.contains_pii]

    def update_asset(self, asset_id: str, updates: Dict[str, Any]) -> bool:
        """Update asset metadata"""
        if asset_id not in self.assets:
            return False
        
        asset = self.assets[asset_id]
        for key, value in updates.items():
            if hasattr(asset, key):
                setattr(asset, key, value)
        
        asset.updated_at = datetime.now().isoformat()
        asset.version += 1
        
        self._save_assets()
        return True

    def add_tags(self, asset_id: str, tags: List[str]) -> bool:
        """Add tags to asset"""
        if asset_id not in self.assets:
            return False
        
        asset = self.assets[asset_id]
        for tag in tags:
            if tag not in asset.tags:
                asset.tags.append(tag)
        
        self._update_tag_index(asset_id, asset.tags)
        self._save_assets()
        return True

    def remove_tags(self, asset_id: str, tags: List[str]) -> bool:
        """Remove tags from asset"""
        if asset_id not in self.assets:
            return False
        
        asset = self.assets[asset_id]
        for tag in tags:
            if tag in asset.tags:
                asset.tags.remove(tag)
        
        self._update_tag_index(asset_id, asset.tags)
        self._save_assets()
        return True

    def get_catalog_report(self) -> Dict[str, Any]:
        """Generate catalog report"""
        total_assets = len(self.assets)
        by_layer = {}
        by_classification = {}
        by_owner = {}
        pii_count = 0
        
        for asset in self.assets.values():
            # By layer
            layer = asset.layer
            by_layer[layer] = by_layer.get(layer, 0) + 1
            
            # By classification
            classification = asset.classification
            by_classification[classification] = by_classification.get(classification, 0) + 1
            
            # By owner
            owner = asset.owner
            if owner not in by_owner:
                by_owner[owner] = []
            by_owner[owner].append(asset.asset_name)
            
            # PII count
            if asset.contains_pii:
                pii_count += 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_assets": total_assets,
            "by_layer": by_layer,
            "by_classification": by_classification,
            "by_owner": by_owner,
            "assets_with_pii": pii_count,
            "unique_owners": len(by_owner),
            "unique_tags": len(self.tags_index),
            "asset_types": self._get_asset_type_distribution()
        }

    def export_catalog(self, export_path: str) -> bool:
        """Export catalog to JSON"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "assets": [asdict(a) for a in self.assets.values()],
                "report": self.get_catalog_report()
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting catalog: {e}")
            return False

    def search_assets(self, query: str) -> List[DataAssetMetadata]:
        """Search assets by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for asset in self.assets.values():
            if (query_lower in asset.asset_name.lower() or
                query_lower in asset.description.lower() or
                any(query_lower in tag.lower() for tag in asset.tags)):
                results.append(asset)
        
        return results

    def _update_tag_index(self, asset_id: str, tags: List[str]):
        """Update tag index"""
        # Remove asset from old tags
        for tag_list in self.tags_index.values():
            if asset_id in tag_list:
                tag_list.remove(asset_id)
        
        # Add to new tags
        for tag in tags:
            if tag not in self.tags_index:
                self.tags_index[tag] = []
            if asset_id not in self.tags_index[tag]:
                self.tags_index[tag].append(asset_id)
        
        self._save_tags_index()

    def _update_owner_index(self, asset_id: str, owner: str):
        """Update owner index"""
        if owner not in self.owners_index:
            self.owners_index[owner] = []
        if asset_id not in self.owners_index[owner]:
            self.owners_index[owner].append(asset_id)
        
        self._save_owners_index()

    def _get_asset_type_distribution(self) -> Dict[str, int]:
        """Get distribution of asset types"""
        distribution = {}
        for asset in self.assets.values():
            distribution[asset.asset_type] = distribution.get(asset.asset_type, 0) + 1
        return distribution

    def _load_assets(self) -> Dict[str, DataAssetMetadata]:
        """Load assets from storage"""
        if not self.assets_file.exists():
            return {}
        
        try:
            with open(self.assets_file, 'r') as f:
                data = json.load(f)
                assets = {}
                for asset_id, asset_data in data.items():
                    # Reconstruct ColumnMetadata objects
                    columns = [ColumnMetadata(**col) for col in asset_data.get('columns', [])]
                    asset_data['columns'] = columns
                    assets[asset_id] = DataAssetMetadata(**asset_data)
                return assets
        except Exception as e:
            print(f"Error loading assets: {e}")
            return {}

    def _load_tags_index(self) -> Dict[str, List[str]]:
        """Load tag index from storage"""
        if not self.tags_index_file.exists():
            return {}
        
        try:
            with open(self.tags_index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading tags index: {e}")
            return {}

    def _load_owners_index(self) -> Dict[str, List[str]]:
        """Load owner index from storage"""
        if not self.owners_index_file.exists():
            return {}
        
        try:
            with open(self.owners_index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading owners index: {e}")
            return {}

    def _save_assets(self):
        """Save assets to storage"""
        try:
            data = {aid: asdict(asset) for aid, asset in self.assets.items()}
            with open(self.assets_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving assets: {e}")

    def _save_tags_index(self):
        """Save tags index to storage"""
        try:
            with open(self.tags_index_file, 'w') as f:
                json.dump(self.tags_index, f, indent=2)
        except Exception as e:
            print(f"Error saving tags index: {e}")

    def _save_owners_index(self):
        """Save owners index to storage"""
        try:
            with open(self.owners_index_file, 'w') as f:
                json.dump(self.owners_index, f, indent=2)
        except Exception as e:
            print(f"Error saving owners index: {e}")


# Global catalog instance
_catalog_instance = None

def get_catalog() -> DataCatalog:
    """Get or create global catalog instance"""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = DataCatalog()
    return _catalog_instance
