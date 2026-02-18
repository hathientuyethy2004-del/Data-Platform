"""
Serving Layer server with optional FastAPI support.
Endpoints:
- POST /query {sql, params} -> runs analytics query via QueryService
- GET /cube/{name} -> returns cube JSON
- GET /health -> returns service health
- GET /metrics -> proxies Monitoring metrics

Optional features: auth token, caching, rate limiting (simple), monitoring hooks.
"""
from typing import Any, Dict, Optional
import threading
import json
import time
from pathlib import Path
import os

# Optional FastAPI
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    import uvicorn
    _FASTAPI_AVAILABLE = True
except Exception:
    FastAPI = None
    HTTPException = Exception
    Request = object
    JSONResponse = None
    _FASTAPI_AVAILABLE = False

from analytics_layer.query_service import get_query_service
from analytics_layer.cube_builder import get_cube_builder
from serving_layer.cache import get_cache

# Monitoring hooks
try:
    from monitoring_layer.metrics.metrics_collector import get_metrics_collector
    metrics = get_metrics_collector()
except Exception:
    metrics = None

# Access control
try:
    from monitoring_layer.access_control import get_access_control
    _ACCESS_CONTROL_AVAILABLE = True
except Exception:
    get_access_control = None
    _ACCESS_CONTROL_AVAILABLE = False

# Optional Redis for persistent rate-limiting
try:
    import redis
    _REDIS_AVAILABLE = True
except Exception:
    redis = None
    _REDIS_AVAILABLE = False

# Simple token-based auth (configurable)
SERVING_TOKEN = None


class ServingLayer:
    def __init__(self, engine: str = "sqlite", db_path: Optional[str] = None):
        self.lock = threading.Lock()
        self.query = get_query_service(db_path=db_path, engine=engine)
        self.cube = get_cube_builder()
        self.cache = get_cache()
        self.rate_limits = {}  # client -> (count, window_start)
        self.rate_limit_per_minute = 120
        self.app = None
        self.engine = engine
        # Redis client for persistent rate limiting (optional)
        self.redis = None
        if _REDIS_AVAILABLE:
            try:
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                self.redis = redis.Redis.from_url(redis_url)
            except Exception:
                self.redis = None

        # Access control instance
        self.acl = None
        if _ACCESS_CONTROL_AVAILABLE:
            try:
                self.acl = get_access_control()
            except Exception:
                self.acl = None

    def start(self, host: str = "0.0.0.0", port: int = 8000):
        if not _FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI not installed. Install via requirements.txt or use the simple_run() method.")

        app = self.build_app()

        uvicorn.run(app, host=host, port=port)

    def build_app(self):
        """Construct and return a FastAPI app instance (useful for tests)."""
        app = FastAPI()

        @app.post('/query')
        async def run_query(payload: Dict[str, Any], request: Request):
            # Basic auth
            token = payload.get('token') or request.headers.get('Authorization')

            # Normalize token header: allow 'Token <user>' or 'Bearer <user>' or plain token
            user = None
            if token:
                if isinstance(token, str):
                    parts = token.split()
                    if len(parts) == 2 and parts[0].lower() in ("token", "bearer"):
                        user = parts[1]
                    else:
                        user = token

            # If a serving token is configured, it must match
            if SERVING_TOKEN and user != SERVING_TOKEN:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # If ACL is present, check permission for query
            if self.acl:
                # If no user provided, deny
                if not user:
                    raise HTTPException(status_code=401, detail="Missing credentials")
                if not self.acl.check_permission(user, 'serve:query'):
                    raise HTTPException(status_code=403, detail="Forbidden")

            sql = payload.get('sql')
            params = payload.get('params')
            use_cache = payload.get('use_cache', True)
            cache_key = f"query:{hash(sql + str(params))}"

            # Rate limit by client IP
            client = request.client.host if hasattr(request, 'client') else 'local'
            if not self._check_rate_limit(client):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            # Check cache
            if use_cache:
                cached = self.cache.get(cache_key)
                if cached:
                    try:
                        if metrics:
                            metrics.increment_counter('serving_query_cache_hits')
                    except Exception:
                        pass
                    return JSONResponse(content=cached)

            # Execute query
            start = time.time()
            res = self.query.execute(sql, tuple(params) if params else None, use_cache=False)
            duration_ms = (time.time() - start) * 1000

            response = {
                'columns': res.columns,
                'rows': res.rows,
                'took_ms': duration_ms
            }

            if use_cache:
                self.cache.set(cache_key, response)

            # Monitoring
            try:
                if metrics:
                    metrics.increment_counter('serving_queries_total', labels={'status': 'success'})
                    metrics.observe_histogram('serving_query_duration_ms', duration_ms)
            except Exception:
                pass

            return JSONResponse(content=response)

        @app.get('/cube/{name}')
        async def get_cube(name: str, request: Request):
            # ACL: require serve:read
            token = None
            try:
                token = request.headers.get('Authorization')
            except Exception:
                token = None
            user = None
            if token and isinstance(token, str):
                parts = token.split()
                if len(parts) == 2 and parts[0].lower() in ("token", "bearer"):
                    user = parts[1]
                else:
                    user = token
            if self.acl:
                if not user or not self.acl.check_permission(user, 'serve:read'):
                    raise HTTPException(status_code=403, detail='Forbidden')

            data = self.cube.load_cube(name)
            if not data:
                raise HTTPException(status_code=404, detail='Cube not found')
            return JSONResponse(content=data)

        @app.get('/health')
        async def health():
            status = {'status': 'ok', 'components': []}
            try:
                status['components'].append({'analytics_query_service': 'ok'})
            except Exception:
                status['components'].append({'analytics_query_service': 'error'})
            try:
                if metrics:
                    status['components'].append({'metrics': 'ok'})
            except Exception:
                status['components'].append({'metrics': 'error'})
            return JSONResponse(content=status)

        @app.get('/metrics')
        async def export_metrics():
            if not metrics:
                raise HTTPException(status_code=404, detail='Metrics not available')
            return JSONResponse(content={'prometheus': metrics.export_prometheus_format()})

        self.app = app
        return app

    def simple_run(self, host: str = '127.0.0.1', port: int = 8080):
        """Fallback simple HTTP server for environments without FastAPI."""
        from http.server import BaseHTTPRequestHandler, HTTPServer
        import urllib.parse as urlparse

        serving = self

        class Handler(BaseHTTPRequestHandler):
            def _set_headers(self, code=200):
                self.send_response(code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()

            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                try:
                    payload = json.loads(body)
                except Exception:
                    payload = {}
                if self.path == '/query':
                    sql = payload.get('sql')
                    params = payload.get('params')
                    res = serving.query.execute(sql, tuple(params) if params else None)
                    self._set_headers(200)
                    self.wfile.write(json.dumps({'columns': res.columns, 'rows': res.rows}).encode())
                    return
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'not found'}).encode())

            def do_GET(self):
                if self.path.startswith('/health'):
                    self._set_headers(200)
                    self.wfile.write(json.dumps({'status': 'ok'}).encode())
                    return
                if self.path.startswith('/metrics'):
                    if not metrics:
                        self._set_headers(404)
                        self.wfile.write(json.dumps({'error': 'metrics unavailable'}).encode())
                        return
                    self._set_headers(200)
                    self.wfile.write(json.dumps({'prometheus': metrics.export_prometheus_format()}).encode())
                    return
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'not found'}).encode())

        server = HTTPServer((host, port), Handler)
        print(f"Serving simple HTTP on {host}:{port}")
        server.serve_forever()

    def _check_rate_limit(self, client: str) -> bool:
        # Prefer Redis-backed counters for persistence
        window = 60
        try:
            if self.redis:
                key = f"rate:{client}"
                # INCR with expiry
                val = self.redis.incr(key)
                if val == 1:
                    self.redis.expire(key, window)
                if val > self.rate_limit_per_minute:
                    return False
                return True
        except Exception:
            pass

        # Fallback in-memory
        now = time.time()
        record = self.rate_limits.get(client)
        if not record:
            self.rate_limits[client] = [1, now]
            return True
        count, start = record
        if now - start > window:
            self.rate_limits[client] = [1, now]
            return True
        if count >= self.rate_limit_per_minute:
            return False
        self.rate_limits[client][0] += 1
        return True


_serving: Optional[ServingLayer] = None

def get_serving_layer(engine: str = "sqlite", db_path: Optional[str] = None) -> ServingLayer:
    global _serving
    if _serving is None:
        _serving = ServingLayer(engine=engine, db_path=db_path)
    return _serving
