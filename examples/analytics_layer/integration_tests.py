"""
Integration tests (smoke) for analytics layer components
"""
from . import get_analytics_manager


def test_query_and_cube():
    mgr = get_analytics_manager()
    q = mgr['query']
    # create a small table
    q.execute("CREATE TABLE IF NOT EXISTS test(a INT, b TEXT);")
    q.execute("INSERT INTO test(a,b) VALUES (1,'x'),(2,'y')")
    res = q.execute("SELECT COUNT(*) FROM test")
    assert res.rows[0][0] == 2

    # Build cube
    cube = mgr['cube']
    cube.build_cube('test_count', 'SELECT COUNT(*) as cnt FROM test')
    c = cube.load_cube('test_count')
    assert c['rows'][0][0] == 2


def test_kpi_engine():
    mgr = get_analytics_manager()
    kpi = mgr['kpi']
    kpi.create_kpi('test_count_kpi', 'Count test', 'SELECT COUNT(*) FROM test', target=1, higher_is_better=True)
    result = kpi.evaluate('test_count_kpi')
    assert result['status'] == 'met'


if __name__ == '__main__':
    test_query_and_cube()
    test_kpi_engine()
    print('Analytics layer smoke tests passed')
