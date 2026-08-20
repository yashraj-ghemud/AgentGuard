"""
Shared type definitions used across modules.

This module contains only truly shared concepts that are used by multiple modules.
Module-specific types should remain in their respective modules.
"""
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Base Types
# ============================================================================

class BaseEntity(BaseModel):
    """Base class for all entities with common fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Result Types
# ============================================================================

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """Generic result type for operations that can succeed or fail."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset from page and page_size."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response structure."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


# ============================================================================
# Status Enums
# ============================================================================

class EntityStatus(str, Enum):
    """Common entity status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ExecutionStatus(str, Enum):
    """Execution status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


# ============================================================================
# Risk Levels
# ============================================================================

class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Request Context
# ============================================================================

class RequestContext(BaseModel):
    """Request context for tracking and correlation."""
    request_id: str
    correlation_id: Optional[str] = None
    user_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Error Response
# ============================================================================

class ErrorDetail(BaseModel):
    """Standard error response structure."""
    code: str
    message: str
    details: Optional[dict] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """API error response wrapper."""
    error: ErrorDetail


# ============================================================================
# Health Check
# ============================================================================

class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    latency_ms: Optional[float] = None


class HealthCheckResponse(BaseModel):
    """Overall health check response."""
    status: HealthStatus
    timestamp: datetime
    version: str
    components: list[ComponentHealth]
