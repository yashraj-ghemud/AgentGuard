"""
Custom exception definitions.

These exceptions provide consistent error handling across modules.
"""
from typing import Optional, Any


class AgentGuardException(Exception):
    """Base exception for all AgentGuard errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


# ============================================================================
# Client Errors (4xx)
# ============================================================================

class ValidationError(AgentGuardException):
    """Validation error (400)."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class UnauthorizedError(AgentGuardException):
    """Unauthorized error (401)."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code="UNAUTHORIZED")


class ForbiddenError(AgentGuardException):
    """Forbidden error (403)."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, code="FORBIDDEN")


class NotFoundError(AgentGuardException):
    """Resource not found error (404)."""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, code="NOT_FOUND", details={"resource": resource, "id": identifier})


class ConflictError(AgentGuardException):
    """Resource conflict error (409)."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="CONFLICT", details=details)


class RateLimitError(AgentGuardException):
    """Rate limit exceeded error (429)."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")


# ============================================================================
# Server Errors (5xx)
# ============================================================================

class InternalError(AgentGuardException):
    """Internal server error (500)."""

    def __init__(self, message: str = "Internal server error", details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="INTERNAL_ERROR", details=details)


class ServiceUnavailableError(AgentGuardException):
    """Service unavailable error (503)."""

    def __init__(self, service: str, message: Optional[str] = None):
        msg = message or f"Service unavailable: {service}"
        super().__init__(msg, code="SERVICE_UNAVAILABLE", details={"service": service})


class DatabaseError(AgentGuardException):
    """Database operation error."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="DATABASE_ERROR", details=details)


# ============================================================================
# Security Errors
# ============================================================================

class SecurityError(AgentGuardException):
    """Security-related error."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="SECURITY_ERROR", details=details)


class SSRFError(SecurityError):
    """SSRF (Server-Side Request Forgery) attempt detected."""

    def __init__(self, url: str, reason: str):
        message = f"SSRF attempt blocked: {reason}"
        super().__init__(message, details={"url": url, "reason": reason})


# ============================================================================
# Business Logic Errors
# ============================================================================

class InvalidStateError(AgentGuardException):
    """Invalid state transition or operation."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="INVALID_STATE", details=details)


class ExecutionError(AgentGuardException):
    """Error during execution."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="EXECUTION_ERROR", details=details)


class TimeoutError(AgentGuardException):
    """Operation timeout."""

    def __init__(self, operation: str, timeout_seconds: int):
        message = f"Operation timed out after {timeout_seconds} seconds: {operation}"
        super().__init__(
            message,
            code="TIMEOUT",
            details={"operation": operation, "timeout_seconds": timeout_seconds},
        )
