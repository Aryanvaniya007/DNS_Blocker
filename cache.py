import time
from collections import OrderedDict

class DNSCache:
    def __init__(self, max_size=10000, default_ttl=300):
        """
        max_size: maximum number of entries to store (LRU eviction)
        default_ttl: fallback TTL (seconds) if we can't extract from response
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl

    def get(self, domain, qtype):
        """Return (response_bytes, ttl_remaining) if found and not expired, else None."""
        key = (domain.lower(), qtype)
        if key in self.cache:
            entry = self.cache[key]
            # Check if expired
            if entry['expiry'] > time.time():
                # Move to end to mark as recently used
                self.cache.move_to_end(key)
                return entry['response']
            else:
                # Remove expired entry
                del self.cache[key]
        return None

    def set(self, domain, qtype, response_bytes, ttl=None):
        """Store a response with a given TTL (or default)."""
        key = (domain.lower(), qtype)
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self.cache[key] = {
            'response': response_bytes,
            'expiry': expiry
        }
        # Move to end (most recent)
        self.cache.move_to_end(key)
        # If over max size, evict oldest (first item)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def clear(self):
        """Clear the entire cache (useful for testing)."""
        self.cache.clear()
