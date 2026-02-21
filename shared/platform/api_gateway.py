"""
Platform API Gateway

Central HTTP entrypoint for product APIs with:
- service registry
- health aggregation
- lightweight request forwarding
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request, Response


@dataclass
class ProductService:
    name: str
    base_url: str
    health_path: str = "/health"
    enabled: bool = True


class APIGateway:
    """API gateway for product-oriented architecture."""

    def __init__(self):
        self.environment = self._load_environment()
        self.services = self._load_services()

    def _load_environment(self) -> str:
        environment = (os.getenv("PLATFORM_ENV") or "dev").strip().lower()
        if environment in {"dev", "staging", "prod"}:
            return environment
        return "dev"

    def _default_services_by_env(self) -> Dict[str, List[ProductService]]:
        return {
            "dev": [
                ProductService("web-user-analytics", "http://127.0.0.1:8002"),
                ProductService("operational-metrics", "http://127.0.0.1:8003"),
                ProductService("compliance-auditing", "http://127.0.0.1:8004"),
            ],
            "staging": [
                ProductService("web-user-analytics", "http://web-user-analytics.staging:8002"),
                ProductService("operational-metrics", "http://operational-metrics.staging:8003"),
                ProductService("compliance-auditing", "http://compliance-auditing.staging:8004"),
            ],
            "prod": [
                ProductService("web-user-analytics", "http://web-user-analytics.prod:8002"),
                ProductService("operational-metrics", "http://operational-metrics.prod:8003"),
                ProductService("compliance-auditing", "http://compliance-auditing.prod:8004"),
            ],
        }

    def _parse_services_payload(self, payload: Any) -> Dict[str, ProductService]:
        parsed: Dict[str, ProductService] = {}
        for item in payload:
            service = ProductService(
                name=item["name"],
                base_url=item["base_url"],
                health_path=item.get("health_path", "/health"),
                enabled=bool(item.get("enabled", True)),
            )
            parsed[service.name] = service
        return parsed

    def _load_services(self) -> Dict[str, ProductService]:
        defaults = self._default_services_by_env()

        # Backward-compatible global override (highest priority)
        raw_json = os.getenv("PLATFORM_PRODUCT_SERVICES_JSON")
        if raw_json:
            try:
                payload = json.loads(raw_json)
                return self._parse_services_payload(payload)
            except (ValueError, KeyError, TypeError):
                pass

        # Env map override (single var containing all envs)
        raw_env_map = os.getenv("PLATFORM_PRODUCT_SERVICES_BY_ENV_JSON")
        try:
            if raw_env_map:
                env_map = json.loads(raw_env_map)
                env_payload = env_map.get(self.environment)
                if env_payload:
                    return self._parse_services_payload(env_payload)
        except (ValueError, KeyError, TypeError):
            pass

        # Env-specific list override
        env_specific_key = f"PLATFORM_PRODUCT_SERVICES_{self.environment.upper()}_JSON"
        raw_env_specific = os.getenv(env_specific_key)
        if raw_env_specific:
            try:
                payload = json.loads(raw_env_specific)
                return self._parse_services_payload(payload)
            except (ValueError, KeyError, TypeError):
                pass

        return {
            service.name: service
            for service in defaults.get(self.environment, defaults["dev"])
        }

    def list_services(self) -> List[Dict[str, Any]]:
        return [asdict(service) for service in self.services.values()]

    def _request(self, method: str, url: str, headers: Dict[str, str], body: bytes | None) -> tuple[int, bytes, str]:
        req = urllib.request.Request(url=url, method=method, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                content_type = resp.headers.get("Content-Type", "application/json")
                return resp.status, resp.read(), content_type
        except urllib.error.HTTPError as exc:
            content_type = exc.headers.get("Content-Type", "application/json") if exc.headers else "application/json"
            return exc.code, exc.read(), content_type
        except urllib.error.URLError as exc:
            raise HTTPException(status_code=502, detail=f"Upstream unavailable: {exc.reason}")

    def service_health(self, service_name: str) -> Dict[str, Any]:
        service = self.services.get(service_name)
        if not service or not service.enabled:
            return {
                "service": service_name,
                "status": "disabled",
                "healthy": False,
            }

        url = f"{service.base_url}{service.health_path}"
        try:
            status, body, _ = self._request("GET", url, {}, None)
            response_payload: Dict[str, Any]
            try:
                response_payload = json.loads(body.decode("utf-8") or "{}")
            except ValueError:
                response_payload = {"raw": body.decode("utf-8", errors="replace")}

            healthy = 200 <= status < 300
            return {
                "service": service_name,
                "status": "up" if healthy else "down",
                "healthy": healthy,
                "upstream_status": status,
                "upstream_response": response_payload,
            }
        except HTTPException as exc:
            return {
                "service": service_name,
                "status": "down",
                "healthy": False,
                "error": str(exc.detail),
            }

    def gateway_health(self) -> Dict[str, Any]:
        details = [self.service_health(name) for name in self.services]
        all_healthy = all(item.get("healthy", False) for item in details if item.get("status") != "disabled")
        return {
            "gateway": "platform-api-gateway",
            "environment": self.environment,
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": details,
        }


api_gateway = APIGateway()

app = FastAPI(
    title="Data Platform API Gateway",
    description="Central gateway for product-oriented data platform",
    version="1.0.0",
)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return api_gateway.gateway_health()


@app.get("/services")
async def services() -> Dict[str, Any]:
    return {
        "environment": api_gateway.environment,
        "count": len(api_gateway.services),
        "services": api_gateway.list_services(),
    }


@app.get("/environment")
async def environment() -> Dict[str, Any]:
    return {
        "environment": api_gateway.environment,
        "supported": ["dev", "staging", "prod"],
        "overrides": {
            "global": "PLATFORM_PRODUCT_SERVICES_JSON",
            "env_map": "PLATFORM_PRODUCT_SERVICES_BY_ENV_JSON",
            "env_specific": f"PLATFORM_PRODUCT_SERVICES_{api_gateway.environment.upper()}_JSON",
        },
    }


@app.get("/services/{service_name}/health")
async def service_health(service_name: str) -> Dict[str, Any]:
    if service_name not in api_gateway.services:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")
    return api_gateway.service_health(service_name)


@app.api_route(
    "/api/{service_name}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy(service_name: str, path: str, request: Request) -> Response:
    service = api_gateway.services.get(service_name)
    if not service or not service.enabled:
        raise HTTPException(status_code=404, detail=f"Unknown or disabled service: {service_name}")

    query_params = dict(request.query_params)
    query_string = f"?{urlencode(query_params)}" if query_params else ""
    upstream_url = f"{service.base_url}/{path}{query_string}"

    body = await request.body()
    filtered_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() in {"content-type", "accept", "authorization", "x-api-key"}
    }

    status, payload, content_type = api_gateway._request(
        method=request.method,
        url=upstream_url,
        headers=filtered_headers,
        body=body if body else None,
    )

    return Response(content=payload, status_code=status, media_type=content_type)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
