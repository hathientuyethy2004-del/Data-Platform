"""
Analytics Layer package
"""
from .query_service import get_query_service
from .aggregation_engine import get_aggregation_engine
from .kpi_engine import get_kpi_engine
from .cube_builder import get_cube_builder
from .connectors.bi_connectors import get_bi_connectors
from .access_control import get_access_control


def get_analytics_manager():
    """Return a simple aggregated analytics manager object"""
    return {
        "query": get_query_service(),
        "aggregation": get_aggregation_engine(),
        "kpi": get_kpi_engine(),
        "cube": get_cube_builder(),
        "connectors": get_bi_connectors(),
        "access": get_access_control()
    }
