from shared.platform.migration_templates.day8_canary_runner import (
    _simulate_canary_distribution,
    build_day8_report,
)


def test_simulate_canary_distribution_close_to_target():
    result = _simulate_canary_distribution(percent=10, total=1000)
    assert result["sample_size"] == 1000
    assert result["within_tolerance"] is True


def test_build_day8_report_pass_for_expected_config():
    env = {
        "OSS_CANARY_WRITE_PERCENT": "10",
        "OSS_CANARY_MODE": "shadow_write",
        "OSS_CANARY_HASH_KEY": "event_id",
        "READ_FROM_OSS_SERVING": "false",
        "DUAL_RUN_ENABLED": "true",
        "DUAL_RUN_COMPARE_ENABLED": "true",
    }
    baseline = {"summary": {"overall_status": "PASS", "critical_issues": 0}}
    smoke = {"overall_status": "PASS"}
    gate = {"summary": {"status": "FAIL", "remaining_hours_to_gate": 10.5}}

    report = build_day8_report(env=env, baseline_report=baseline, smoke_report=smoke, gate_report=gate)

    assert report["summary"]["status"] == "PASS"
    assert report["checks"]["canary_write_percent_is_10"]["status"] == "PASS"
    assert report["checks"]["read_path_stays_legacy"]["status"] == "PASS"


def test_build_day8_report_fail_when_read_from_oss_enabled():
    env = {
        "OSS_CANARY_WRITE_PERCENT": "10",
        "READ_FROM_OSS_SERVING": "true",
        "DUAL_RUN_ENABLED": "true",
        "DUAL_RUN_COMPARE_ENABLED": "true",
    }
    baseline = {"summary": {"overall_status": "PASS", "critical_issues": 0}}
    smoke = {"overall_status": "PASS"}
    gate = {"summary": {"status": "FAIL", "remaining_hours_to_gate": 10.5}}

    report = build_day8_report(env=env, baseline_report=baseline, smoke_report=smoke, gate_report=gate)

    assert report["summary"]["status"] == "FAIL"
    assert report["checks"]["read_path_stays_legacy"]["status"] == "FAIL"
