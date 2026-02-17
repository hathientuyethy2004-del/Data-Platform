"""
Data Lineage System
Tracks data flow and transformations across the platform for end-to-end visibility
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import uuid

from config.governance_config import governance_config


@dataclass
class LineageEdge:
    """Represents a lineage relationship"""
    edge_id: str
    source_asset: str
    target_asset: str
    transformation_job: str
    operation_type: str  # transform, aggregate, load, copy, join, etc.
    job_name: str = ""
    job_description: str = ""
    created_at: str = ""
    created_by: str = ""

    def __post_init__(self):
        if not self.edge_id:
            self.edge_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class ColumnLineage:
    """Column-level lineage"""
    target_column: str
    target_asset: str
    source_columns: List[Dict[str, str]]  # [{"asset": "...", "column": "..."}, ...]
    transformation_logic: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class DataLineageTracker:
    """Data lineage tracking system"""

    def __init__(self):
        """Initialize lineage tracker"""
        self.storage_path = Path(governance_config.lineage.lineage_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.lineage_file = self.storage_path / "lineage_edges.json"
        self.column_lineage_file = self.storage_path / "column_lineage.json"
        
        self.edges: Dict[str, LineageEdge] = self._load_lineage()
        self.column_lineages: List[ColumnLineage] = self._load_column_lineage()

    def record_lineage(self, source_asset: str, target_asset: str,
                      transformation_job: str, operation_type: str,
                      created_by: str = "system") -> str:
        """Record a lineage relationship"""
        edge = LineageEdge(
            edge_id=str(uuid.uuid4()),
            source_asset=source_asset,
            target_asset=target_asset,
            transformation_job=transformation_job,
            operation_type=operation_type,
            created_by=created_by
        )
        
        self.edges[edge.edge_id] = edge
        self._save_lineage()
        
        return edge.edge_id

    def record_column_lineage(self, target_asset: str, target_column: str,
                             source_columns: List[Dict[str, str]],
                             transformation_logic: str = "") -> bool:
        """Record column-level lineage"""
        col_lineage = ColumnLineage(
            target_asset=target_asset,
            target_column=target_column,
            source_columns=source_columns,
            transformation_logic=transformation_logic
        )
        
        self.column_lineages.append(col_lineage)
        self._save_column_lineage()
        
        return True

    def get_upstream_lineage(self, asset_id: str, depth: int = -1) -> Dict[str, any]:
        """Get all upstream dependencies (sources) for an asset"""
        upstream = {
            "asset": asset_id,
            "direct_sources": [],
            "all_sources": set(),
            "lineage_graph": {}
        }
        
        self._traverse_upstream(asset_id, upstream["direct_sources"], upstream["all_sources"])
        upstream["all_sources"] = list(upstream["all_sources"])
        
        return upstream

    def get_downstream_lineage(self, asset_id: str) -> Dict[str, any]:
        """Get all downstream dependents (consumers) for an asset"""
        downstream = {
            "asset": asset_id,
            "direct_consumers": [],
            "all_consumers": set(),
            "lineage_graph": {}
        }
        
        self._traverse_downstream(asset_id, downstream["direct_consumers"], downstream["all_consumers"])
        downstream["all_consumers"] = list(downstream["all_consumers"])
        
        return downstream

    def get_impact_analysis(self, asset_id: str) -> Dict[str, any]:
        """Analyze impact of changes to an asset"""
        downstream = self.get_downstream_lineage(asset_id)
        upstream = self.get_upstream_lineage(asset_id)
        
        # Find directly affected assets
        directly_affected = []
        for edge in self.edges.values():
            if edge.source_asset == asset_id:
                directly_affected.append({
                    "asset": edge.target_asset,
                    "job": edge.transformation_job,
                    "operation": edge.operation_type
                })
        
        return {
            "asset": asset_id,
            "impact_level": self._calculate_impact_level(downstream),
            "directly_affected_count": len(directly_affected),
            "transitively_affected_count": len(downstream["all_consumers"]),
            "directly_affected_assets": directly_affected,
            "all_affected_assets": downstream["all_consumers"],
            "estimated_update_time": self._estimate_update_cascade_time(asset_id)
        }

    def get_lineage_graph(self, asset_id: str, depth: int = 2) -> Dict[str, any]:
        """Get complete lineage graph for visualization"""
        visited = set()
        nodes = []
        edges = []
        
        self._build_graph(asset_id, depth, 0, visited, nodes, edges, "both")
        
        return {
            "root_asset": asset_id,
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    def get_lineage_report(self) -> Dict[str, any]:
        """Generate lineage report"""
        # Find sources and sinks
        all_sources = set(e.source_asset for e in self.edges.values())
        all_targets = set(e.target_asset for e in self.edges.values())
        
        sources = all_sources - all_targets  # Assets with no incoming lineage
        sinks = all_targets - all_sources    # Assets with no outgoing lineage
        
        transformations = {}
        for edge in self.edges.values():
            op = edge.operation_type
            transformations[op] = transformations.get(op, 0) + 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_lineage_edges": len(self.edges),
            "source_assets": list(sources),
            "sink_assets": list(sinks),
            "transformation_types": transformations,
            "column_lineages": len(self.column_lineages),
            "most_complex_assets": self._get_most_complex_assets(top_n=10)
        }

    def export_lineage(self, export_path: str) -> bool:
        """Export lineage to JSON"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "edges": [asdict(e) for e in self.edges.values()],
                "column_lineages": [asdict(c) for c in self.column_lineages],
                "report": self.get_lineage_report()
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting lineage: {e}")
            return False

    def _traverse_upstream(self, asset_id: str, direct: List, all_upstream: Set):
        """Traverse upstream dependencies"""
        for edge in self.edges.values():
            if edge.target_asset == asset_id:
                direct.append({
                    "source": edge.source_asset,
                    "job": edge.transformation_job,
                    "operation": edge.operation_type
                })
                all_upstream.add(edge.source_asset)
                # Recursive call for transitive dependencies
                self._traverse_upstream(edge.source_asset, [], all_upstream)

    def _traverse_downstream(self, asset_id: str, direct: List, all_downstream: Set):
        """Traverse downstream dependencies"""
        for edge in self.edges.values():
            if edge.source_asset == asset_id:
                direct.append({
                    "target": edge.target_asset,
                    "job": edge.transformation_job,
                    "operation": edge.operation_type
                })
                all_downstream.add(edge.target_asset)
                # Recursive call for transitive dependencies
                self._traverse_downstream(edge.target_asset, [], all_downstream)

    def _calculate_impact_level(self, downstream: Dict) -> str:
        """Calculate impact level based on downstream assets"""
        count = len(downstream["all_consumers"])
        if count == 0:
            return "low"
        elif count <= 5:
            return "medium"
        else:
            return "high"

    def _estimate_update_cascade_time(self, asset_id: str) -> Dict[str, int]:
        """Estimate time to update cascade through downstream assets"""
        # Simplified estimation: 5 min per level of cascading
        return {
            "direct_update_minutes": 5,
            "full_cascade_minutes": self._calculate_cascade_depth(asset_id) * 5
        }

    def _calculate_cascade_depth(self, asset_id: str, depth: int = 0) -> int:
        """Calculate maximum cascade depth"""
        max_depth = depth
        for edge in self.edges.values():
            if edge.source_asset == asset_id:
                sub_depth = self._calculate_cascade_depth(edge.target_asset, depth + 1)
                max_depth = max(max_depth, sub_depth)
        return max_depth

    def _build_graph(self, asset_id: str, max_depth: int, current_depth: int,
                    visited: Set, nodes: List, edges: List, direction: str):
        """Build lineage graph recursively"""
        if current_depth >= max_depth or asset_id in visited:
            return
        
        visited.add(asset_id)
        
        # Add node
        nodes.append({
            "id": asset_id,
            "label": asset_id,
            "depth": current_depth
        })
        
        if direction in ["both", "upstream"]:
            for edge in self.edges.values():
                if edge.target_asset == asset_id:
                    edges.append({
                        "source": edge.source_asset,
                        "target": asset_id,
                        "label": edge.operation_type
                    })
                    self._build_graph(edge.source_asset, max_depth, current_depth + 1,
                                    visited, nodes, edges, direction)
        
        if direction in ["both", "downstream"]:
            for edge in self.edges.values():
                if edge.source_asset == asset_id:
                    edges.append({
                        "source": asset_id,
                        "target": edge.target_asset,
                        "label": edge.operation_type
                    })
                    self._build_graph(edge.target_asset, max_depth, current_depth + 1,
                                    visited, nodes, edges, direction)

    def _get_most_complex_assets(self, top_n: int = 10) -> List[Dict[str, any]]:
        """Get most complex assets (by number of connections)"""
        asset_complexity = {}
        
        for edge in self.edges.values():
            asset_complexity[edge.source_asset] = asset_complexity.get(edge.source_asset, 0) + 1
            asset_complexity[edge.target_asset] = asset_complexity.get(edge.target_asset, 0) + 1
        
        sorted_assets = sorted(asset_complexity.items(), key=lambda x: x[1], reverse=True)
        return [{"asset": a, "connections": c} for a, c in sorted_assets[:top_n]]

    def _load_lineage(self) -> Dict[str, LineageEdge]:
        """Load lineage from storage"""
        if not self.lineage_file.exists():
            return {}
        
        try:
            with open(self.lineage_file, 'r') as f:
                data = json.load(f)
                return {eid: LineageEdge(**edata) for eid, edata in data.items()}
        except Exception as e:
            print(f"Error loading lineage: {e}")
            return {}

    def _load_column_lineage(self) -> List[ColumnLineage]:
        """Load column lineage from storage"""
        if not self.column_lineage_file.exists():
            return []
        
        try:
            with open(self.column_lineage_file, 'r') as f:
                data = json.load(f)
                return [ColumnLineage(**cdata) for cdata in data]
        except Exception as e:
            print(f"Error loading column lineage: {e}")
            return []

    def _save_lineage(self):
        """Save lineage to storage"""
        try:
            data = {eid: asdict(edge) for eid, edge in self.edges.items()}
            with open(self.lineage_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving lineage: {e}")

    def _save_column_lineage(self):
        """Save column lineage to storage"""
        try:
            data = [asdict(c) for c in self.column_lineages]
            with open(self.column_lineage_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving column lineage: {e}")


# Global lineage tracker instance
_lineage_tracker = None

def get_lineage_tracker() -> DataLineageTracker:
    """Get or create global lineage tracker instance"""
    global _lineage_tracker
    if _lineage_tracker is None:
        _lineage_tracker = DataLineageTracker()
    return _lineage_tracker
