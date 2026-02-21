from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Tuple

NULL_LIKE_VALUES = {"", "null", "none", "n/a", "na", "nil", "undefined"}


def normalize_null(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in NULL_LIKE_VALUES:
        return None
    return value


def normalize_timestamp(value: Any) -> Any:
    value = normalize_null(value)
    if value is None:
        return None
    if not isinstance(value, str):
        return value

    raw = value.strip()
    if not raw:
        return None

    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return value

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.isoformat()


def normalize_numeric(value: Any, scale: int = 6) -> Any:
    value = normalize_null(value)
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float, Decimal)):
        quant = Decimal("1." + ("0" * scale))
        return float(Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP))

    return value


def normalize_record(
    record: Dict[str, Any],
    required_fields: Iterable[str] | None = None,
    defaults: Dict[str, Any] | None = None,
    timestamp_fields: Iterable[str] | None = None,
    numeric_fields: Iterable[str] | None = None,
    numeric_scale: int = 6,
) -> Dict[str, Any]:
    defaults = defaults or {}
    timestamp_fields = set(timestamp_fields or [])
    numeric_fields = set(numeric_fields or [])

    normalized = dict(record)

    for key, value in list(normalized.items()):
        value = normalize_null(value)
        if key in timestamp_fields:
            value = normalize_timestamp(value)
        if key in numeric_fields:
            value = normalize_numeric(value, numeric_scale)
        normalized[key] = value

    if required_fields:
        for field in required_fields:
            if field not in normalized:
                normalized[field] = defaults.get(field)

    return normalized


def compare_records(
    legacy: Dict[str, Any],
    oss: Dict[str, Any],
    timestamp_fields: Iterable[str] | None = None,
    numeric_fields: Iterable[str] | None = None,
    required_fields: Iterable[str] | None = None,
    defaults: Dict[str, Any] | None = None,
    numeric_scale: int = 6,
) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    left = normalize_record(
        legacy,
        required_fields=required_fields,
        defaults=defaults,
        timestamp_fields=timestamp_fields,
        numeric_fields=numeric_fields,
        numeric_scale=numeric_scale,
    )
    right = normalize_record(
        oss,
        required_fields=required_fields,
        defaults=defaults,
        timestamp_fields=timestamp_fields,
        numeric_fields=numeric_fields,
        numeric_scale=numeric_scale,
    )

    keys = set(left.keys()) | set(right.keys())
    diffs: Dict[str, Dict[str, Any]] = {}
    for key in sorted(keys):
        if left.get(key) != right.get(key):
            diffs[key] = {"legacy": left.get(key), "oss": right.get(key)}

    return len(diffs) == 0, diffs
