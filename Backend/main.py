"""
Main FastAPI application entry point.

This module initializes the FastAPI application with all necessary
middleware, routers, and configuration.
"""
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import time
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from core.config.settings import get_settings
from core.observability.logging import setup_logging, get_logger, bind_context, clear_context
from shared.exceptions import AgentGuardException
from shared.types import ErrorResponse, ErrorDetail, HealthCheckResponse, HealthStatus, ComponentHealth
from shared.utils import generate_request_id, utc_now

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting AgentGuard",
        extra={
            "version": settings.app_version,
            "environment": settings.app_env,
        },
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down AgentGuard")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Automated Red-Teaming & Reliability Engineering for AI Agents",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ============================================================================
# Middleware
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

_rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def security_boundary_middleware(request: Request, call_next):
    """Apply cheap edge protections before application handlers run."""
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > settings.max_request_size_bytes:
        return JSONResponse(status_code=413, content={"error": {"code": "REQUEST_TOO_LARGE", "message": "Request body exceeds configured limit"}})

    if settings.rate_limit_enabled:
        client = request.client.host if request.client else "unknown"
        if len(_rate_limit_buckets) > 10_000:
            _rate_limit_buckets.clear()
        now = time.monotonic()
        bucket = _rate_limit_buckets[client]
        cutoff = now - 60
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute:
            response = JSONResponse(status_code=429, content={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}})
            response.headers["Retry-After"] = "60"
            return response
        bucket.append(now)

    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """
    Middleware to add request context (request ID, timing, etc.).
    """
    request_id = generate_request_id()
    
    # Bind context for logging
    bind_context(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        clear_context()


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(AgentGuardException)
async def agentguard_exception_handler(
    request: Request, exc: AgentGuardException
) -> JSONResponse:
    """Handle custom AgentGuard exceptions."""
    logger.error(
        f"AgentGuard exception: {exc.message}",
        extra={
            "code": exc.code,
            "details": exc.details,
            "path": request.url.path,
        },
    )
    
    status_code_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
        "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "SERVICE_UNAVAILABLE": status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    
    status_code = status_code_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details if exc.details else None,
            request_id=getattr(request.state, "request_id", None),
        )
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        "Validation error",
        extra={
            "errors": exc.errors(),
            "path": request.url.path,
        },
    )
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": exc.errors()},
            request_id=getattr(request.state, "request_id", None),
        )
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(
        "Unexpected exception",
        extra={
            "path": request.url.path,
            "exception": str(exc),
        },
    )
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred" if settings.is_production else str(exc),
            request_id=getattr(request.state, "request_id", None),
        )
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


# ============================================================================
# Health Check
# ============================================================================

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Health check endpoint",
)
async def health_check() -> HealthCheckResponse:
    """
    Check application health and component status.
    
    Returns:
        Health check response with component statuses
    """
    components = [
        ComponentHealth(
            name="api",
            status=HealthStatus.HEALTHY,
            message="API is running",
        ),
    ]
    
    # Determine overall status
    overall_status = HealthStatus.HEALTHY
    if any(c.status == HealthStatus.UNHEALTHY for c in components):
        overall_status = HealthStatus.UNHEALTHY
    elif any(c.status == HealthStatus.DEGRADED for c in components):
        overall_status = HealthStatus.DEGRADED
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=utc_now(),
        version=settings.app_version,
        components=components,
    )


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint with basic info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "docs_url": "/docs",
    }


# ============================================================================
# API Router Registration
# ============================================================================

# Import module routers
from modules.agent_registry.interface.routes import router as agent_router
from modules.agent_versioning.interface.routes import router as version_router
from modules.tool_registry.interface.routes import router as tool_router
from modules.agent_intelligence.interface.routes import router as intelligence_router
from modules.risk_analysis.interface.routes import router as risk_router
from modules.test_strategy.interface.routes import router as strategy_router
from modules.scenario_generation.interface.routes import router as scenario_router
from modules.evaluation.interface.routes import router as evaluation_router

# Register routers
app.include_router(agent_router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(
    version_router,
    prefix="/api/v1/agents/{agent_id}/versions",
    tags=["Agent Versions"],
)
app.include_router(
    tool_router,
    prefix="/api/v1/agents/{agent_id}/tools",
    tags=["Tools"],
)
# Global tool endpoints (for direct tool access by ID)
app.include_router(
    tool_router,
    prefix="/api/v1/tools",
    tags=["Tools"],
)
# Part 2: Agent Intelligence (Module 04)
app.include_router(intelligence_router, tags=["Agent Intelligence"])
# Part 2: Risk Analysis (Module 05)
app.include_router(risk_router, tags=["Risk Analysis"])
# Part 2: Test Strategy (Module 06)
app.include_router(strategy_router, tags=["Test Strategy"])
# Part 2: Scenario Generation (Module 07)
app.include_router(scenario_router, tags=["Scenario Generation"])
# Part 3: Execution and Evaluation
app.include_router(evaluation_router, tags=["Execution & Evaluation"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
