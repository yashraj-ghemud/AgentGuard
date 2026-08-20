"""Compatibility adapter for legacy string-based domain event calls.

The platform event bus uses typed ``DomainEvent`` instances and async delivery.
Part 2 scenario-generation code predates that contract and publishes a string plus
payload synchronously. This adapter keeps those calls observable while the module
is migrated incrementally.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.events.local_publisher import get_event_publisher


class EventPublisher:
    """Record legacy events and expose them for diagnostics and migration."""

    def __init__(self) -> None:
        self._typed_publisher = get_event_publisher()
        self.events: list[Dict[str, Any]] = []

    def publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        event = {
            "event_type": event_type,
            "payload": payload or {},
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        self.events.append(event)

    def clear(self) -> None:
        self.events.clear()
