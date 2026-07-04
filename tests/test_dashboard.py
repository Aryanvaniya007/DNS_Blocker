import json
import pytest
from dashboard import app, stats

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_dashboard_index(client):
    # Log a dummy query to ensure there is some data
    stats.log_query("test-dashboard.com", blocked=True, cached=False)
    
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "DNS Blocker Dashboard" in html
    assert "test-dashboard.com" in html

def test_dashboard_api(client):
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_queries' in data
    assert 'blocked' in data
    assert 'block_rate' in data
    assert 'cache_hit_rate' in data
