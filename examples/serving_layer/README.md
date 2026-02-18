# Serving Layer

This serving layer exposes analytics functionality over HTTP/REST with optional FastAPI support.

Features:
- Query endpoint (`/query`) to run SQL against the configured analytics engine (SQLite/DuckDB)
- Cube retrieval endpoint (`/cube/{name}`)
- Health and metrics endpoints (`/health`, `/metrics`)
- Simple in-memory + file-backed cache
- Optional FastAPI/uvicorn runtime, with a simple built-in fallback server
- Rate limiting and token-based auth hooks
- Integration with `monitoring_layer` metrics when available

Quick start (FastAPI):

```bash
pip install -r requirements.txt
# optionally install fastapi and uvicorn
pip install fastapi uvicorn
python -c "from platform.bootstrap import start_platform_services; start_platform_services(); from serving_layer.server import get_serving_layer; get_serving_layer().start()"
```

Fallback simple server:

```bash
python -c "from platform.bootstrap import start_platform_services; start_platform_services(); from serving_layer.server import get_serving_layer; get_serving_layer().simple_run()"
```

Run test:

```bash
pytest serving_layer/tests/test_server.py -q
```
