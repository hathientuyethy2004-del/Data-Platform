from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class APIClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response = requests.request(
            method=method.upper(),
            url=f"{self.base_url}/{path.lstrip('/')}",
            headers=headers,
            json=json_payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        if "application/json" in response.headers.get("Content-Type", ""):
            return response.json()
        return {"text": response.text}
