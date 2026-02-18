"""
Cube Builder
Simple materialized cube builder for pre-aggregations persisted as JSON files.
"""
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from .query_service import get_query_service


class CubeBuilder:
    def __init__(self):
        self.storage = Path("analytics_data/cubes")
        self.storage.mkdir(parents=True, exist_ok=True)
        self.query = get_query_service()

    def build_cube(self, cube_name: str, sql: str) -> bool:
        """Execute aggregation SQL and store results as JSON for fast access"""
        res = self.query.execute(sql, use_cache=False)
        rows = [list(r) for r in res.rows]
        data = {"cube_name": cube_name, "generated_at": datetime.now().isoformat(), "columns": res.columns, "rows": rows}
        with open(self.storage / f"{cube_name}.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
        return True

    def load_cube(self, cube_name: str) -> Dict[str, Any]:
        path = self.storage / f"{cube_name}.json"
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return json.load(f)


_cube_builder: CubeBuilder = None

def get_cube_builder() -> CubeBuilder:
    global _cube_builder
    if _cube_builder is None:
        _cube_builder = CubeBuilder()
    return _cube_builder
