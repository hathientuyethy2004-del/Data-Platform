"""
Register a lightweight aggregation job that uses MonitoringIntegration to register component and expose metrics.
"""
from analytics_layer import get_analytics_manager
from monitoring_layer.integration.platform_integration import get_monitoring_integration
import time


def sample_aggregation():
    # A small aggregation that writes a cube
    mgr = get_analytics_manager()
    cube = mgr['cube']
    # Example SQL: count rows in a table 'events' if exists
    try:
        cube.build_cube('events_count_job', 'SELECT COUNT(*) as cnt FROM events')
        return {'rows': 1}
    except Exception as e:
        return {'error': str(e)}


def register_and_run():
    # Ensure monitoring integration is up
    mon = get_monitoring_integration()
    mon.register_component('aggregation_job_runner', 'service')

    agg = get_analytics_manager()['aggregation']
    agg.register_job('events_count_job', 'Count events and build cube', sample_aggregation, schedule_minutes=1)

    # Run once now
    status = agg.run_job_now('events_count_job')
    print('Job status:', status)


if __name__ == '__main__':
    register_and_run()
