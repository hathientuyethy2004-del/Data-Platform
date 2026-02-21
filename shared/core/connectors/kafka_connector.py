from __future__ import annotations

from typing import Any, Dict, Optional


class KafkaConnector:
    def __init__(self, bootstrap_servers: str, group_id: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id

    def build_consumer_config(self) -> Dict[str, Any]:
        config: Dict[str, Any] = {
            "bootstrap_servers": self.bootstrap_servers,
            "auto_offset_reset": "latest",
            "enable_auto_commit": True,
        }
        if self.group_id:
            config["group_id"] = self.group_id
        return config
