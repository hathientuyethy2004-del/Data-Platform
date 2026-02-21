from shared.platform.migration_templates.day27_validation_runner import evaluate_day27_validation


def _day25_26(status: str = "READ_PATH_100_LEGACY_DRAINING", applied: bool = True):
    return {
        "summary": {
            "status": status,
        },
        "read_cutover": {
            "applied": applied,
        },
    }


def _env(
    regression: bool = True,
    performance: bool = True,
    p95: float = 420,
    p99: float = 980,
    err_pct: float = 0.2,
    slo: bool = True,
    alerts: bool = True,
    audit: bool = True,
):
    return {
        "REGRESSION_SUITE_PASS": "true" if regression else "false",
        "PERFORMANCE_SUITE_PASS": "true" if performance else "false",
        "PERF_P95_MS": str(p95),
        "PERF_P99_MS": str(p99),
        "PERF_ERROR_RATE_PCT": str(err_pct),
        "SLO_DASHBOARD_PASS": "true" if slo else "false",
        "ALERTS_PASS": "true" if alerts else "false",
        "AUDIT_LOGS_PASS": "true" if audit else "false",
    }


def test_day27_validation_passes_when_all_checks_pass():
    report = evaluate_day27_validation(
        day25_26_report=_day25_26("READ_PATH_100_LEGACY_DRAINING", True),
        env27=_env(),
    )

    assert report["summary"]["status"] == "VALIDATED_FOR_FREEZE"
    assert report["summary"]["ready_for_day28"] is True
    assert report["validation"]["blockers"] == []


def test_day27_validation_blocked_when_day25_26_not_ready():
    report = evaluate_day27_validation(
        day25_26_report=_day25_26("BLOCKED", False),
        env27=_env(),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "day25_26_read_cutover_required" in report["validation"]["blockers"]


def test_day27_validation_blocked_when_performance_guardrails_fail():
    report = evaluate_day27_validation(
        day25_26_report=_day25_26("READ_PATH_100_LEGACY_DRAINING", True),
        env27=_env(p95=650, p99=1400, err_pct=1.7),
    )

    assert report["summary"]["status"] == "BLOCKED"
    assert "performance_guardrails" in report["validation"]["blockers"]
