"""
Serving Layer package
"""
from .server import get_serving_layer
from .cache import get_cache


def get_serving_manager():
    return {
        "server": get_serving_layer(),
        "cache": get_cache()
    }
