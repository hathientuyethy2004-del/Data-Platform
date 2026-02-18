"""
Metadata API Module
"""

from .metadata_manager import (
    get_metadata_manager,
    MetadataManager,
    DataAsset,
    AssetType,
    DataClassification,
    DataQualityMetrics
)

__all__ = [
    'get_metadata_manager',
    'MetadataManager',
    'DataAsset',
    'AssetType',
    'DataClassification',
    'DataQualityMetrics'
]
