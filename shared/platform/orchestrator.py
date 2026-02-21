"""
Platform Orchestrator

Central orchestration utilities for product discovery, architecture validation,
and optional command execution per product.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProductDescriptor:
    name: str
    path: Path
    has_src: bool
    has_serving: bool
    has_processing: bool
    has_monitoring: bool
    test_path: Optional[Path]


class PlatformOrchestrator:
    """Platform-level orchestrator for product discovery and health checks."""

    def __init__(self, workspace_root: Optional[Path] = None):
        env_workspace = os.getenv("WORKSPACE_ROOT")
        self.workspace_root = workspace_root or Path(env_workspace or "/workspaces/Data-Platform")
        self.products_root = self.workspace_root / "products"

    def discover_products(self) -> List[ProductDescriptor]:
        """Discover product directories and basic architecture completeness."""
        if not self.products_root.exists():
            return []

        descriptors: List[ProductDescriptor] = []
        for product_dir in sorted(self.products_root.iterdir()):
            if not product_dir.is_dir():
                continue

            src_dir = product_dir / "src"
            serving_dir = src_dir / "serving"
            processing_dir = src_dir / "processing"
            monitoring_dir = src_dir / "monitoring"
            test_dir = src_dir / "tests"

            descriptors.append(
                ProductDescriptor(
                    name=product_dir.name,
                    path=product_dir,
                    has_src=src_dir.exists(),
                    has_serving=serving_dir.exists(),
                    has_processing=processing_dir.exists(),
                    has_monitoring=monitoring_dir.exists(),
                    test_path=test_dir if test_dir.exists() else None,
                )
            )

        return descriptors

    def architecture_status(self) -> Dict[str, Any]:
        """Return a snapshot of platform architecture readiness."""
        products = self.discover_products()

        product_status = []
        for product in products:
            architecture_complete = (
                product.has_src
                and product.has_serving
                and product.has_processing
                and product.has_monitoring
            )
            product_status.append(
                {
                    "name": product.name,
                    "path": str(product.path),
                    "has_src": product.has_src,
                    "has_serving": product.has_serving,
                    "has_processing": product.has_processing,
                    "has_monitoring": product.has_monitoring,
                    "has_tests": product.test_path is not None,
                    "architecture_complete": architecture_complete,
                }
            )

            complete_count = sum(1 for item in product_status if item["architecture_complete"])
            incomplete_products = [item["name"] for item in product_status if not item["architecture_complete"]]

        shared_platform = self.workspace_root / "shared" / "platform"
        shared_tests = self.workspace_root / "shared" / "tests"
        infrastructure = self.workspace_root / "infrastructure"

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workspace_root": str(self.workspace_root),
            "products_total": len(products),
            "products_complete": complete_count,
            "products_incomplete": len(products) - complete_count,
            "incomplete_products": incomplete_products,
            "products": product_status,
            "platform_components": {
                "shared_platform_exists": shared_platform.exists(),
                "orchestrator_exists": (shared_platform / "orchestrator.py").exists(),
                "api_gateway_exists": (shared_platform / "api_gateway.py").exists(),
                "shared_tests_exists": shared_tests.exists(),
                "infrastructure_exists": infrastructure.exists(),
            },
        }

    def run_product_tests(self, product_name: str, timeout_seconds: int = 300) -> Dict[str, Any]:
        """Run pytest for a specific product if tests exist."""
        product_path = self.products_root / product_name
        test_path = product_path / "src" / "tests"
        if not test_path.exists():
            return {
                "product": product_name,
                "status": "skipped",
                "reason": "No src/tests directory found",
            }

        command = ["pytest", "-q", str(test_path)]
        try:
            run_env = os.environ.copy()
            existing_pythonpath = run_env.get("PYTHONPATH", "").strip()
            run_env["PYTHONPATH"] = "." if not existing_pythonpath else f".:{existing_pythonpath}"
            result = subprocess.run(
                command,
                cwd=str(product_path),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                env=run_env,
            )
            return {
                "product": product_name,
                "status": "success" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "product": product_name,
                "status": "failed",
                "reason": f"Timed out after {timeout_seconds}s",
            }

    def run_demo_if_available(self, product_name: str, timeout_seconds: int = 300) -> Dict[str, Any]:
        """Run demo script for product when available."""
        product_path = self.products_root / product_name
        demo_script = product_path / "demo_run.py"
        if not demo_script.exists():
            return {
                "product": product_name,
                "status": "skipped",
                "reason": "No demo_run.py found",
            }

        command = ["python", str(demo_script)]
        try:
            run_env = os.environ.copy()
            existing_pythonpath = run_env.get("PYTHONPATH", "").strip()
            run_env["PYTHONPATH"] = "." if not existing_pythonpath else f".:{existing_pythonpath}"
            result = subprocess.run(
                command,
                cwd=str(product_path),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                env=run_env,
            )
            return {
                "product": product_name,
                "status": "success" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "product": product_name,
                "status": "failed",
                "reason": f"Timed out after {timeout_seconds}s",
            }



def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Data Platform - Platform Orchestrator")
    parser.add_argument(
        "--workspace-root",
        default=None,
        help="Workspace root path (default: WORKSPACE_ROOT env or /workspaces/Data-Platform)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Show platform architecture status")
    status_parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero exit code if any product is architecture_incomplete",
    )

    test_parser = subparsers.add_parser("test", help="Run product tests")
    test_parser.add_argument("product", help="Product name under products/")
    test_parser.add_argument(
        "--allow-skip",
        action="store_true",
        help="Treat skipped tests as success (exit code 0)",
    )

    demo_parser = subparsers.add_parser("demo", help="Run product demo if available")
    demo_parser.add_argument("product", help="Product name under products/")
    demo_parser.add_argument(
        "--allow-skip",
        action="store_true",
        help="Treat skipped demo as success (exit code 0)",
    )

    return parser



def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    orchestrator = PlatformOrchestrator(
        workspace_root=Path(args.workspace_root) if args.workspace_root else None
    )

    if args.command == "status":
        status = orchestrator.architecture_status()
        print(json.dumps(status, indent=2))
        if getattr(args, "strict", False) and status.get("products_incomplete", 0) > 0:
            return 2
        return 0

    if args.command == "test":
        result = orchestrator.run_product_tests(args.product)
        print(json.dumps(result, indent=2))
        if result.get("status") == "success":
            return 0
        if result.get("status") == "skipped":
            return 0 if getattr(args, "allow_skip", False) else 3
        return 1

    if args.command == "demo":
        result = orchestrator.run_demo_if_available(args.product)
        print(json.dumps(result, indent=2))
        if result.get("status") == "success":
            return 0
        if result.get("status") == "skipped":
            return 0 if getattr(args, "allow_skip", False) else 3
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
