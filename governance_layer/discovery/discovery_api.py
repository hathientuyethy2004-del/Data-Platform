"""
Data Discovery API
FastAPI endpoints for searching, browsing, and discovering data assets
"""

import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from config.governance_config import governance_config
from catalog.data_catalog import get_catalog, DataAssetMetadata
from lineage.lineage_tracker import get_lineage_tracker
from quality.quality_monitor import get_quality_monitor
from access.access_control import get_access_manager

try:
    from fastapi import FastAPI, Query, HTTPException, Header
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    limit: int = 10
    offset: int = 0


class AssetResponse(BaseModel):
    """Asset response model"""
    asset_id: str
    name: str
    asset_type: str
    layer: str
    owner: str
    description: str
    tags: List[str]
    classification: str
    contains_pii: bool
    quality_score: Optional[float] = None


class LineageResponse(BaseModel):
    """Lineage response model"""
    asset_id: str
    upstream_assets: List[str]
    downstream_assets: List[str]
    impact_level: str
    affected_count: int


class DataDiscoveryAPI:
    """Data discovery and exploration API"""

    def __init__(self, port: int = 8889):
        """Initialize discovery API"""
        self.port = port
        self.catalog = get_catalog()
        self.lineage = get_lineage_tracker()
        self.quality = get_quality_monitor()
        self.access_manager = get_access_manager()
        
        self.storage_path = Path(governance_config.discovery.search_index_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        if FASTAPI_AVAILABLE:
            self.app = FastAPI(
                title="Data Discovery API",
                description="Browse and search data assets in the platform",
                version="1.0.0"
            )
            self._setup_routes()
        else:
            self.app = None
            print("FastAPI not available - API endpoints will not be created")

    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "Data Discovery API"
            }
        
        @self.app.get("/search", response_model=Dict)
        async def search_assets(
            query: str = Query(..., description="Search query"),
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0),
            api_key: str = Header(None)
        ):
            """Search for data assets"""
            # Verify API key
            if api_key and not self._verify_api_key(api_key):
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            try:
                results = self.catalog.search_assets(query)
                
                # Paginate results
                total = len(results)
                paginated = results[offset:offset + limit]
                
                return {
                    "query": query,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "results": [
                        {
                            "asset_id": asset.asset_id,
                            "name": asset.name,
                            "type": asset.asset_type,
                            "layer": asset.layer,
                            "owner": asset.owner,
                            "description": asset.description[:200] if asset.description else "",
                            "tags": asset.tags,
                            "classification": asset.classification
                        }
                        for asset in paginated
                    ]
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/assets", response_model=Dict)
        async def browse_assets(
            layer: Optional[str] = Query(None),
            owner: Optional[str] = Query(None),
            classification: Optional[str] = Query(None),
            tag: Optional[str] = Query(None),
            api_key: str = Header(None)
        ):
            """Browse assets with filters"""
            if api_key and not self._verify_api_key(api_key):
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            try:
                results = []
                
                if layer:
                    results = self.catalog.get_assets_by_layer(layer)
                elif owner:
                    results = self.catalog.get_assets_by_owner(owner)
                elif classification:
                    results = self.catalog.get_assets_by_classification(classification)
                elif tag:
                    results = self.catalog.get_assets_by_tag(tag)
                else:
                    # Get all assets
                    results = list(self.catalog._catalog_instance.values()) if hasattr(self.catalog, '_catalog_instance') else []
                
                return {
                    "filter": {
                        "layer": layer,
                        "owner": owner,
                        "classification": classification,
                        "tag": tag
                    },
                    "total": len(results),
                    "assets": [
                        {
                            "asset_id": asset.asset_id,
                            "name": asset.name,
                            "type": asset.asset_type,
                            "layer": asset.layer,
                            "owner": asset.owner,
                            "classification": asset.classification,
                            "record_count": asset.technical_details.record_count if asset.technical_details else 0
                        }
                        for asset in results
                    ]
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/assets/{asset_id}", response_model=Dict)
        async def get_asset_details(
            asset_id: str,
            api_key: str = Header(None)
        ):
            """Get detailed asset information"""
            if api_key and not self._verify_api_key(api_key):
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            try:
                asset = self.catalog.get_asset(asset_id)
                
                if not asset:
                    raise HTTPException(status_code=404, detail="Asset not found")
                
                # Get quality score
                quality = self.quality.get_quality_status(asset_id)
                
                return {
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "type": asset.asset_type,
                    "layer": asset.layer,
                    "platform": asset.platform,
                    "location": asset.location,
                    "owner": asset.owner,
                    "owner_email": asset.owner_email,
                    "owner_team": asset.owner_team,
                    "description": asset.description,
                    "tags": asset.tags,
                    "classification": asset.classification,
                    "contains_pii": asset.contains_pii,
                    "pii_columns": asset.pii_columns,
                    "technical_details": {
                        "record_count": asset.technical_details.record_count if asset.technical_details else 0,
                        "size_bytes": asset.technical_details.size_bytes if asset.technical_details else 0,
                        "columns": len(asset.technical_details.columns) if asset.technical_details else 0
                    },
                    "quality_score": quality.get("scorecard", {}).get("overall_score") if quality else None,
                    "freshness_sla": {
                        "update_frequency": asset.freshness_slas.update_frequency if asset.freshness_slas else "",
                        "sla_hours": asset.freshness_slas.sla_freshness_hours if asset.freshness_slas else 0
                    } if asset.freshness_slas else None,
                    "metadata": {
                        "created_at": asset.metadata_created_at,
                        "updated_at": asset.metadata_updated_at,
                        "created_by": asset.metadata_created_by,
                        "version": asset.metadata_version
                    }
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/assets/{asset_id}/lineage", response_model=Dict)
        async def get_asset_lineage(
            asset_id: str,
            direction: str = Query("both", regex="^(upstream|downstream|both)$"),
            depth: int = Query(3, ge=1, le=10),
            api_key: str = Header(None)
        ):
            """Get lineage for an asset"""
            if api_key and not self._verify_api_key(api_key):
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            try:
                asset = self.catalog.get_asset(asset_id)
                if not asset:
                    raise HTTPException(status_code=404, detail="Asset not found")
                
                lineage_data = {
                    "asset_id": asset_id,
                    "asset_name": asset.name,
                    "timestamp": datetime.now().isoformat()
                }
                
                if direction in ["upstream", "both"]:
                    upstream = self.lineage.get_upstream_lineage(asset_id, depth)
                    lineage_data["upstream"] = {
                        "direct_sources": upstream.get("direct_sources", []),
                        "all_sources": upstream.get("all_sources", []),
                        "source_count": len(upstream.get("all_sources", []))
                    }
                
                if direction in ["downstream", "both"]:
                    downstream = self.lineage.get_downstream_lineage(asset_id)
                    lineage_data["downstream"] = {
                        "direct_consumers": downstream.get("direct_consumers", []),
                        "all_consumers": downstream.get("all_consumers", []),
                        "consumer_count": len(downstream.get("all_consumers", []))
                    }
                
                # Impact analysis
                impact = self.lineage.get_impact_analysis(asset_id)
                lineage_data["impact_analysis"] = {
                    "impact_level": impact.get("impact_level"),
                    "directly_affected": impact.get("directly_affected_count", 0),
                    "transitively_affected": impact.get("transitively_affected_count", 0),
                    "estimated_update_time_minutes": impact.get("estimated_update_time", 0)
                }
                
                return lineage_data
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/assets/{asset_id}/similar", response_model=Dict)
        async def get_similar_assets(
            asset_id: str,
            limit: int = Query(5, ge=1, le=20),
            api_key: str = Header(None)
        ):
            """Get similar assets"""
            if api_key and not self._verify_api_key(api_key):
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            try:
                asset = self.catalog.get_asset(asset_id)
                if not asset:
                    raise HTTPException(status_code=404, detail="Asset not found")
                
                # Find similar by tags, layer, and owner
                similar = []
                
                # Get assets with same tags
                for tag in asset.tags:
                    tagged = self.catalog.get_assets_by_tag(tag)
                    similar.extend([a for a in tagged if a.asset_id != asset_id])
                
                # Get assets in same layer
                layer_assets = self.catalog.get_assets_by_layer(asset.layer)
                similar.extend([a for a in layer_assets if a.asset_id != asset_id])
                
                # Deduplicate and limit
                unique_similar = {a.asset_id: a for a in similar}.values()
                limited = list(unique_similar)[:limit]
                
                return {
                    "asset_id": asset_id,
                    "total_similar": len(unique_similar),
                    "returned": len(limited),
                    "similar_assets": [
                        {
                            "asset_id": a.asset_id,
                            "name": a.name,
                            "layer": a.layer,
                            "owner": a.owner,
                            "tags": a.tags,
                            "similarity_reason": "shared_tags_or_layer"
                        }
                        for a in limited
                    ]
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/catalog/report", response_model=Dict)
        async def get_catalog_report(api_key: str = Header(None)):
            """Get catalog report"""
            if api_key and not self._verify_api_key(api_key):
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            try:
                report = self.catalog.get_catalog_report()
                return report
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/quality/report", response_model=Dict)
        async def get_quality_report(
            days: int = Query(30, ge=1, le=365),
            api_key: str = Header(None)
        ):
            """Get quality report"""
            if api_key and not self._verify_api_key(api_key):
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            try:
                report = self.quality.get_quality_report(days=days)
                return report
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def _verify_api_key(self, api_key: str) -> bool:
        """Verify API key format"""
        try:
            key_id, key = api_key.split(":", 1)
            return self.access_manager.validate_api_key(key_id, key)
        except Exception:
            return False

    def start(self):
        """Start the API server"""
        if not FASTAPI_AVAILABLE:
            print("FastAPI not available. Install with: pip install fastapi uvicorn")
            return
        
        if self.app is None:
            print("API not initialized")
            return
        
        try:
            import uvicorn
            print(f"Starting Data Discovery API on port {self.port}")
            print(f"API Docs: http://localhost:{self.port}/docs")
            uvicorn.run(self.app, host="0.0.0.0", port=self.port)
        except ImportError:
            print("Uvicorn not available. Install with: pip install uvicorn")

    def export_api_spec(self, export_path: str) -> bool:
        """Export API specification"""
        try:
            if not self.app:
                return False
            
            spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Data Discovery API",
                    "version": "1.0.0",
                    "description": "API for searching and discovering data assets"
                },
                "servers": [{"url": f"http://localhost:{self.port}"}],
                "paths": {
                    "/search": {
                        "get": {
                            "summary": "Search for data assets",
                            "parameters": [
                                {"name": "query", "in": "query", "required": True, "schema": {"type": "string"}},
                                {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 10}},
                                {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                                {"name": "api_key", "in": "header", "schema": {"type": "string"}}
                            ]
                        }
                    },
                    "/assets": {
                        "get": {
                            "summary": "Browse assets with filters",
                            "parameters": [
                                {"name": "layer", "in": "query", "schema": {"type": "string"}},
                                {"name": "owner", "in": "query", "schema": {"type": "string"}},
                                {"name": "classification", "in": "query", "schema": {"type": "string"}},
                                {"name": "tag", "in": "query", "schema": {"type": "string"}},
                                {"name": "api_key", "in": "header", "schema": {"type": "string"}}
                            ]
                        }
                    },
                    "/assets/{asset_id}": {
                        "get": {
                            "summary": "Get asset details",
                            "parameters": [
                                {"name": "asset_id", "in": "path", "required": True, "schema": {"type": "string"}},
                                {"name": "api_key", "in": "header", "schema": {"type": "string"}}
                            ]
                        }
                    },
                    "/assets/{asset_id}/lineage": {
                        "get": {
                            "summary": "Get asset lineage",
                            "parameters": [
                                {"name": "asset_id", "in": "path", "required": True, "schema": {"type": "string"}},
                                {"name": "direction", "in": "query", "schema": {"type": "string", "enum": ["upstream", "downstream", "both"]}},
                                {"name": "depth", "in": "query", "schema": {"type": "integer", "default": 3}}
                            ]
                        }
                    },
                    "/assets/{asset_id}/similar": {
                        "get": {
                            "summary": "Get similar assets",
                            "parameters": [
                                {"name": "asset_id", "in": "path", "required": True, "schema": {"type": "string"}},
                                {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 5}}
                            ]
                        }
                    },
                    "/catalog/report": {
                        "get": {
                            "summary": "Get catalog statistics report"
                        }
                    },
                    "/quality/report": {
                        "get": {
                            "summary": "Get quality monitoring report",
                            "parameters": [
                                {"name": "days", "in": "query", "schema": {"type": "integer", "default": 30}}
                            ]
                        }
                    }
                }
            }
            
            with open(export_path, 'w') as f:
                json.dump(spec, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting API spec: {e}")
            return False


# Global discovery API instance
_discovery_api = None

def get_discovery_api(port: int = 8889) -> DataDiscoveryAPI:
    """Get or create global discovery API"""
    global _discovery_api
    if _discovery_api is None:
        _discovery_api = DataDiscoveryAPI(port=port)
    return _discovery_api
