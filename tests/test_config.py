from config import Config

def test_config_defaults():
    config = Config('nonexistent.yaml')
    assert config.get('server.port') == 5353
    assert config.get('upstream_dns')[0] == '8.8.8.8'

def test_config_override():
    # Use config_data to simulate a custom config
    config = Config(config_data={'server': {'port': 9999}})
    assert config.get('server.port') == 9999
