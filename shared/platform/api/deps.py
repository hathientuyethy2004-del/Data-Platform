from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from fastapi import Request


def build_meta(request: Request) -> Dict[str, str]:
    request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex[:12]}")
    return {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def ok_response(data: Any, request: Request) -> Dict[str, Any]:
    return {
        "data": data,
        "meta": build_meta(request),
    }


def error_response(
    *,
    request: Request,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "meta": build_meta(request),
    }
