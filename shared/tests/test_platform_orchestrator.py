from pathlib import Path

from shared.platform.orchestrator import PlatformOrchestrator


def test_architecture_status_contains_summary_fields():
    orchestrator = PlatformOrchestrator(workspace_root=Path("/workspaces/Data-Platform"))
    status = orchestrator.architecture_status()

    assert "products_complete" in status
    assert "products_incomplete" in status
    assert "incomplete_products" in status
    assert status["products_total"] >= status["products_complete"]


def test_status_marks_user_segmentation_as_complete_after_skeleton_update():
    orchestrator = PlatformOrchestrator(workspace_root=Path("/workspaces/Data-Platform"))
    status = orchestrator.architecture_status()

    names = {product["name"]: product for product in status["products"]}
    assert "user-segmentation" in names
    assert names["user-segmentation"]["architecture_complete"] is True


def test_run_product_tests_injects_pythonpath_for_src_imports(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    product_tests = workspace / "products" / "demo-product" / "src" / "tests"
    product_tests.mkdir(parents=True)

    orchestrator = PlatformOrchestrator(workspace_root=workspace)

    captured_env = {}

    class DummyResult:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(*args, **kwargs):
        captured_env.update(kwargs.get("env", {}))
        return DummyResult()

    monkeypatch.setenv("PYTHONPATH", "custom_path")
    monkeypatch.setattr("shared.platform.orchestrator.subprocess.run", fake_run)

    result = orchestrator.run_product_tests("demo-product")

    assert result["status"] == "success"
    assert captured_env.get("PYTHONPATH") == ".:custom_path"
