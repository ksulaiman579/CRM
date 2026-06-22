import time
import logging

logger = logging.getLogger(__name__)

class TTLCache:
    """
    A simple thread-safe, in-memory TTL Cache.
    """
    def __init__(self):
        self._store = {}

    def get(self, key: str):
        if key in self._store:
            value, expires_at = self._store[key]
            if time.time() < expires_at:
                return value
            else:
                # Expired
                del self._store[key]
        return None

    def set(self, key: str, value: any, ttl_seconds: int = 300):
        expires_at = time.time() + ttl_seconds
        self._store[key] = (value, expires_at)
        
    def delete(self, key: str):
        if key in self._store:
            del self._store[key]
            
    def clear(self):
        self._store.clear()

# Global cache instance
cache = TTLCache()
