from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class MigrationFlags:
    use_oss_ingestion: bool
    use_oss_quality: bool
    use_oss_serving: bool
    read_from_oss_serving: bool
    dual_run_enabled: bool
    dual_run_compare_enabled: bool

    @classmethod
    def from_env(cls) -> "MigrationFlags":
        return cls(
            use_oss_ingestion=_env_bool("USE_OSS_INGESTION", False),
            use_oss_quality=_env_bool("USE_OSS_QUALITY", False),
            use_oss_serving=_env_bool("USE_OSS_SERVING", False),
            read_from_oss_serving=_env_bool("READ_FROM_OSS_SERVING", False),
            dual_run_enabled=_env_bool("DUAL_RUN_ENABLED", False),
            dual_run_compare_enabled=_env_bool("DUAL_RUN_COMPARE_ENABLED", True),
        )
