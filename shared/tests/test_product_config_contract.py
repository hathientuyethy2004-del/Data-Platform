from pathlib import Path

import yaml


REQUIRED_TOP_LEVEL_KEYS = {
    "product",
    "sla",
    "serving",
    "monitoring",
    "access_control",
    "environments",
}


def _load_yaml(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file_handle:
        return yaml.safe_load(file_handle) or {}


def test_all_product_configs_follow_minimum_contract():
    config_paths = sorted(Path("/workspaces/Data-Platform/products").glob("*/config/product_config.yaml"))
    assert config_paths, "No product_config.yaml files found"

    missing = {}
    for config_path in config_paths:
        data = _load_yaml(config_path)
        missing_keys = sorted(REQUIRED_TOP_LEVEL_KEYS - set(data.keys()))
        if missing_keys:
            missing[str(config_path)] = missing_keys

    assert not missing, f"Config contract violations: {missing}"
