"""Publishes domain events to the Redis queue consumed by the notifier service."""
import json
import logging
from datetime import UTC, datetime

import redis

from ..config import settings

log = logging.getLogger(__name__)
_client: redis.Redis | None = None


def _redis() -> redis.Redis | None:
    global _client
    if not settings.redis_url:
        return None
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
    return _client


def publish(event_type: str, **payload) -> None:
    client = _redis()
    if client is None:
        return
    message = {"type": event_type, "at": datetime.now(UTC).isoformat(), **payload}
    try:
        client.rpush(settings.events_queue, json.dumps(message))
    except redis.RedisError:
        log.warning("Could not publish %s event", event_type, exc_info=True)
