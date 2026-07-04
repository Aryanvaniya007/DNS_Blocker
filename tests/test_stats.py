import os
import json
import pytest
from stats import Stats

def test_stats_initialization():
    stats = Stats(save_file=None)
    assert stats.total_queries == 0
    assert stats.blocked_count == 0
    assert stats.cache_hits == 0
    assert stats.cache_misses == 0
    assert len(stats.top_blocked) == 0

def test_stats_log_query():
    stats = Stats(save_file=None)
    stats.log_query("example.com", blocked=False, cached=False)
    stats.log_query("ads.google.com", blocked=True, cached=False)
    stats.log_query("example.com", blocked=False, cached=True)

    summary = stats.get_summary()
    assert summary['total_queries'] == 3
    assert summary['blocked'] == 1
    assert summary['block_rate'] == 33.33
    assert summary['cache_hits'] == 1
    assert summary['cache_misses'] == 2
    assert summary['cache_hit_rate'] == 33.33
    assert summary['top_10'] == [("ads.google.com", 1)]

def test_stats_save_load(tmp_path):
    save_file = tmp_path / "test_stats.json"
    stats = Stats(save_file=str(save_file))
    stats.log_query("blocked.com", blocked=True, cached=False)
    stats.save()

    # Load in a new stats instance
    new_stats = Stats(save_file=str(save_file))
    assert new_stats.total_queries == 1
    assert new_stats.blocked_count == 1
    assert "blocked.com" in new_stats.top_blocked
