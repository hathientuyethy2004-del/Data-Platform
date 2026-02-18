from serving_layer.server import get_serving_layer


def test_get_serving_layer_instance():
    s = get_serving_layer()
    assert s is not None
    assert hasattr(s, 'query')
    assert hasattr(s, 'cache')

if __name__ == '__main__':
    print('Running serving layer smoke test')
    test_get_serving_layer_instance()
    print('OK')
