from shared.platform.migration_templates.day13_chaos_runner import run_day13_chaos


def test_day13_chaos_report_has_required_sections():
    report = run_day13_chaos()
    assert "scenarios" in report
    assert "integrity" in report
    assert "summary" in report
    assert report["summary"]["scenarios_total"] == 3


def test_day13_chaos_passes_with_current_simulation():
    report = run_day13_chaos()
    assert report["summary"]["status"] == "PASS"
    assert report["summary"]["integrity_passed"] is True
    assert report["summary"]["scenarios_passed"] == report["summary"]["scenarios_total"]
