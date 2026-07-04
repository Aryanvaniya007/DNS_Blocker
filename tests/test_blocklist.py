import pytest
from blocklist import Blocklist

def test_blocklist_exact_match():
    bl = Blocklist()
    bl.domains.add('example.com')
    assert bl.is_blocked('example.com') is True

def test_blocklist_subdomain():
    bl = Blocklist()
    bl.domains.add('example.com')
    assert bl.is_blocked('ads.example.com') is True

def test_blocklist_no_match():
    bl = Blocklist()
    bl.domains.add('example.com')
    assert bl.is_blocked('google.com') is False

def test_blocklist_load_from_url(monkeypatch):
    # Mock requests.get to avoid real network call
    import requests
    class MockResponse:
        text = "0.0.0.0 test.com\n127.0.0.1 localhost\n# comment\n||evil.com^\n"
    def mock_get(*args, **kwargs):
        return MockResponse()
    monkeypatch.setattr(requests, 'get', mock_get)

    bl = Blocklist()
    bl.load_from_url('fake')
    assert 'test.com' in bl.domains
    assert 'evil.com' in bl.domains
    assert 'localhost' in bl.domains  # hosts format
