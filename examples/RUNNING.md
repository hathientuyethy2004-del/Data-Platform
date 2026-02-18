# Running the Data-Platform locally

Prerequisites
- Python 3.11+
- git

1. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Set an available serving port and start the platform (uses local packages)

Choose a free port (e.g. 9000). Start the platform package:

```bash
PYTHONPATH=. SERVING_PORT=9000 python -m platform_pkg.app &
```

This starts background platform services (aggregation scheduler) and the FastAPI server.

3. Smoke-check the endpoints

Health:

```bash
curl http://127.0.0.1:9000/health
```

Metrics:

```bash
curl http://127.0.0.1:9000/metrics
```

Run a query (replace token with your ACL token if configured):

```bash
curl -X POST http://127.0.0.1:9000/query \
  -H "Content-Type: application/json" \
  -d '{"sql":"CREATE TABLE items (id INTEGER, name TEXT);", "token":"local-test-token"}'
```

4. Notes
- If ports 8000/8081/9000 are occupied, choose another free port and set `SERVING_PORT`.
- For secure Redis, provision a Kubernetes Secret or use Vault/SealedSecrets; do not commit credentials.
- To run end-to-end tests in CI, the GitHub Actions workflow installs `requirements.txt` so tests/integration/test_end_to_end.py will execute there.

Xây dựng ERROR HANDLING & DLQ và TESTING INFRASTRUCTURE