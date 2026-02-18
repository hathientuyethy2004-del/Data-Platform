"""Platform app launcher (uses platform_pkg to avoid stdlib name collision)."""
from pathlib import Path
import importlib.util
import os


def _load_bootstrap_and_start(metrics_storage_path=None):
    p = Path(__file__).with_name('bootstrap.py')
    spec = importlib.util.spec_from_file_location('local_bootstrap', p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.start_platform_services(metrics_storage_path)
    except Exception:
        pass


def main():
    _load_bootstrap_and_start()

    engine = os.getenv('ANALYTICS_ENGINE', 'sqlite')
    db_path = os.getenv('ANALYTICS_DB', ':memory:')

    from serving_layer.server import get_serving_layer

    serving = get_serving_layer(engine=engine, db_path=db_path)

    try:
        host = os.getenv('SERVING_HOST', '0.0.0.0')
        port = int(os.getenv('SERVING_PORT', '8000'))
        serving.start(host=host, port=port)
    except RuntimeError:
        serving.simple_run()


if __name__ == '__main__':
    main()
