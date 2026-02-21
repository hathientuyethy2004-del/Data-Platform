from shared.platform.migration_templates.compare_utils import (
    compare_records,
    normalize_null,
    normalize_numeric,
    normalize_timestamp,
)


def test_normalize_null_variants():
    assert normalize_null("") is None
    assert normalize_null("NULL") is None
    assert normalize_null("n/a") is None
    assert normalize_null("value") == "value"


def test_normalize_timestamp_to_utc():
    assert normalize_timestamp("2026-02-21T12:00:00Z") == "2026-02-21T12:00:00+00:00"
    assert normalize_timestamp("2026-02-21T12:00:00") == "2026-02-21T12:00:00+00:00"


def test_normalize_numeric_rounding():
    assert normalize_numeric(1.23456789, scale=4) == 1.2346
    assert normalize_numeric(10, scale=4) == 10.0


def test_compare_records_handles_schema_timezone_rounding_and_null_semantics():
    legacy = {
        "event_id": "evt-1",
        "event_ts": "2026-02-21T12:00:00Z",
        "metric_value": 1.23456789,
        "country": "",
    }
    oss = {
        "event_id": "evt-1",
        "event_ts": "2026-02-21T12:00:00+00:00",
        "metric_value": 1.234568,
        "country": None,
        "device_type": "desktop",
    }

    ok, diffs = compare_records(
        legacy,
        oss,
        required_fields=["event_id", "event_ts", "metric_value", "country", "device_type"],
        defaults={"device_type": "desktop"},
        timestamp_fields=["event_ts"],
        numeric_fields=["metric_value"],
        numeric_scale=6,
    )

    assert ok is True
    assert diffs == {}
