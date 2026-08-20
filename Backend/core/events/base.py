"""
Event system base definitions.

This module provides the foundation for domain events and event handling.
Events enable loose coupling between modules.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from shared.utils import generate_id, utc_now


# ============================================================================
# Base Event
# ============================================================================

class DomainEvent(BaseModel):
    """
    Base class for all domain events.
    
    Domain events represent something that happened in the system
    that other parts of the system might care about.
    """
    event_id: UUID = Field(default_factory=generate_id)
    event_type: str
    timestamp: datetime = Field(default_factory=utc_now)
    correlation_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True  # Events are immutable


# ============================================================================
# Event Handler
# ============================================================================

EventHandler = Callable[[DomainEvent], None]


class IEventPublisher(ABC):
    """
    Interface for event publishers.
    
    Implementations can use different mechanisms:
    - In-memory (synchronous)
    - Redis Pub/Sub
    - Kafka
    - RabbitMQ
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event.
        
        Args:
            event: Domain event to publish
        """
        pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event is published
        """
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        pass
