"""
Local in-memory event publisher.

This is a simple event bus for development and single-instance deployments.
For production multi-instance deployments, replace with Redis/Kafka implementation.
"""
import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional

from core.events.base import DomainEvent, EventHandler, IEventPublisher

logger = logging.getLogger(__name__)


class LocalEventPublisher(IEventPublisher):
    """
    In-memory event publisher for local development.
    
    Events are published synchronously to all registered handlers.
    This implementation does NOT persist events or work across multiple processes.
    
    For production use, replace with a distributed event bus (Redis, Kafka, etc.).
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish event to all registered handlers.
        
        Args:
            event: Domain event to publish
        """
        event_type = event.event_type
        
        async with self._lock:
            handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers registered for event type: {event_type}")
            return

        logger.info(
            f"Publishing event: {event_type}",
            extra={
                "event_id": str(event.event_id),
                "event_type": event_type,
                "correlation_id": event.correlation_id,
            },
        )

        # Call handlers (synchronously for now)
        for handler in handlers:
            try:
                # If handler is async, await it
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event_type}: {e}",
                    exc_info=True,
                    extra={
                        "event_id": str(event.event_id),
                        "event_type": event_type,
                        "handler": handler.__name__,
                    },
                )

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event is published
        """
        logger.info(
            f"Subscribing handler to event type: {event_type}",
            extra={"event_type": event_type, "handler": handler.__name__},
        )
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.info(
                    f"Unsubscribed handler from event type: {event_type}",
                    extra={"event_type": event_type, "handler": handler.__name__},
                )
            except ValueError:
                logger.warning(
                    f"Handler not found for event type: {event_type}",
                    extra={"event_type": event_type, "handler": handler.__name__},
                )

    def clear_handlers(self, event_type: Optional[str] = None) -> None:
        """
        Clear handlers for a specific event type or all event types.
        
        Args:
            event_type: Event type to clear handlers for. If None, clear all.
        """
        if event_type:
            self._handlers[event_type].clear()
            logger.info(f"Cleared handlers for event type: {event_type}")
        else:
            self._handlers.clear()
            logger.info("Cleared all event handlers")


# Global event publisher instance
_event_publisher: Optional[LocalEventPublisher] = None


def get_event_publisher() -> LocalEventPublisher:
    """Get global event publisher instance."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = LocalEventPublisher()
    return _event_publisher


def reset_event_publisher() -> None:
    """Reset event publisher (useful for testing)."""
    global _event_publisher
    if _event_publisher:
        _event_publisher.clear_handlers()
    _event_publisher = None
