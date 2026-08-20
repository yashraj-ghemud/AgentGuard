"""
Structured logging configuration.

Uses structlog for structured, context-aware logging.
"""
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import FilteringBoundLogger

from core.config.settings import get_settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    Sets up structlog with:
    - JSON formatting in production
    - Human-readable formatting in development
    - Request ID and correlation ID tracking
    - Timestamp and log level
    """
    settings = get_settings()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # Shared processors for all logging
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_format == "json":
        # JSON formatting for production
        renderer = structlog.processors.JSONRenderer()
    else:
        # Human-readable formatting for development
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure handler for standard library loggers
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared_processors,
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Bound logger instance
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Bind context variables to all subsequent log messages.
    
    Args:
        **kwargs: Context variables to bind
        
    Example:
        bind_context(request_id="abc123", user_id="user456")
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """
    Unbind context variables.
    
    Args:
        *keys: Context variable keys to unbind
        
    Example:
        unbind_context("request_id", "user_id")
    """
    structlog.contextvars.unbind_contextvars(*keys)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


def log_context(**kwargs: Any) -> Dict[str, Any]:
    """
    Create a logging context dictionary.
    
    Args:
        **kwargs: Context key-value pairs
        
    Returns:
        Dictionary of context values
    """
    return kwargs
