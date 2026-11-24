from app.cache.base import Cache
from app.cache.memory import MemoryCache
from app.config import settings

_memory_cache = MemoryCache()


def get_cache() -> Cache:
    match settings.cache_backend:
        case "memory":
            return _memory_cache
        case other:
            raise ValueError(f"unknown cache backend: {other}")  # Phase 2 加 "redis"
