import time
from cache import DNSCache

def test_cache_set_get():
    cache = DNSCache(max_size=10, default_ttl=60)
    cache.set('example.com', 1, b'response_data', ttl=10)
    assert cache.get('example.com', 1) == b'response_data'

def test_cache_expiry():
    cache = DNSCache(default_ttl=1)
    cache.set('example.com', 1, b'data', ttl=1)
    time.sleep(1.5)
    assert cache.get('example.com', 1) is None

def test_cache_eviction():
    cache = DNSCache(max_size=2)
    cache.set('a.com', 1, b'1')
    cache.set('b.com', 1, b'2')
    cache.set('c.com', 1, b'3')  # should evict oldest (a.com)
    assert cache.get('a.com', 1) is None
    assert cache.get('b.com', 1) is not None
    assert cache.get('c.com', 1) is not None
