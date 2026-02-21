"""
Platform Orchestrator

Central orchestration utilities for product discovery, architecture validation,
and optional command execution per product.
"""

from __future__ import annotations

import argparse
import json
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
        self.workspace_root = workspace_root or Path("/workspaces/Data-Platform")
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

        shared_platform = self.workspace_root / "shared" / "platform"
        shared_tests = self.workspace_root / "shared" / "tests"
        infrastructure = self.workspace_root / "infrastructure"

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workspace_root": str(self.workspace_root),
            "products_total": len(products),
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
            result = subprocess.run(
                command,
                cwd=str(product_path),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
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
            result = subprocess.run(
                command,
                cwd=str(product_path),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
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
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show platform architecture status")

    test_parser = subparsers.add_parser("test", help="Run product tests")
    test_parser.add_argument("product", help="Product name under products/")

    demo_parser = subparsers.add_parser("demo", help="Run product demo if available")
    demo_parser.add_argument("product", help="Product name under products/")

    return parser



def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    orchestrator = PlatformOrchestrator()

    if args.command == "status":
        print(json.dumps(orchestrator.architecture_status(), indent=2))
        return 0

    if args.command == "test":
        print(json.dumps(orchestrator.run_product_tests(args.product), indent=2))
        return 0

    if args.command == "demo":
        print(json.dumps(orchestrator.run_demo_if_available(args.product), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
