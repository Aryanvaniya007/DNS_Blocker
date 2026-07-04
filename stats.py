import time
import json
from collections import Counter, defaultdict
from datetime import datetime
import threading

class Stats:
    def __init__(self, save_file="stats.json"):
        self.save_file = save_file
        self.lock = threading.Lock()
        self.total_queries = 0
        self.blocked_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.top_blocked = Counter()
        self.timeline = defaultdict(int)
        self.start_time = time.time()
        self.last_save_time = time.time()
        # Only load if save_file is not None
        if self.save_file is not None:
            self._load()

    def _load(self):
        if self.save_file is None:
            return
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
                self.total_queries = data.get('total_queries', 0)
                self.blocked_count = data.get('blocked_count', 0)
                self.cache_hits = data.get('cache_hits', 0)
                self.cache_misses = data.get('cache_misses', 0)
                self.top_blocked = Counter(data.get('top_blocked', {}))
                self.timeline = defaultdict(int, data.get('timeline', {}))
                self.start_time = data.get('start_time', time.time())
                self.last_save_time = time.time()
        except FileNotFoundError:
            pass

    def save(self):
        if self.save_file is None:
            return
        with self.lock:
            data = {
                'total_queries': self.total_queries,
                'blocked_count': self.blocked_count,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'top_blocked': dict(self.top_blocked),
                'timeline': dict(self.timeline),
                'start_time': self.start_time
            }
        with open(self.save_file, 'w') as f:
            json.dump(data, f, indent=2)

    def log_query(self, domain, blocked=False, cached=False):
        should_save = False
        with self.lock:
            self.total_queries += 1
            if cached:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
            if blocked:
                self.blocked_count += 1
                self.top_blocked[domain] += 1
            hour = datetime.now().strftime("%Y-%m-%d %H:00")
            self.timeline[hour] += 1
            
            # Auto-save every 10 seconds
            now = time.time()
            if now - self.last_save_time >= 10:
                self.last_save_time = now
                should_save = True
        
        if should_save:
            self.save()

    def get_summary(self):
        with self.lock:
            uptime = time.time() - self.start_time
            block_rate = round(self.blocked_count / max(1, self.total_queries) * 100, 2)
            hours = sorted(self.timeline.keys())[-24:]
            timeline_data = {h: self.timeline[h] for h in hours}
            return {
                'total_queries': self.total_queries,
                'blocked': self.blocked_count,
                'block_rate': block_rate,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': round(self.cache_hits / max(1, self.cache_hits + self.cache_misses) * 100, 2),
                'top_10': self.top_blocked.most_common(10),
                'timeline': timeline_data,
                'uptime': int(uptime)
            }

# Global instance (will be overridden by dns_blocker.py with config)
stats = Stats()
