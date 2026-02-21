from pathlib import Path
from typing import Any, Dict

import yaml


def load_yaml_config(path: str | Path) -> Dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file_handle:
        data = yaml.safe_load(file_handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping config in {config_path}")
    return data
