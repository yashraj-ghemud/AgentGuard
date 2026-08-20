"""
HTTP Execution Provider.

Executes agents via HTTP/HTTPS endpoints with SSRF protection
and comprehensive security controls.
"""
import time
from typing import Optional

import httpx

from core.execution.provider import (
    IExecutionProvider,
    ExecutionRequest,
    ExecutionResult,
)
from core.execution.ssrf_protection import get_ssrf_protection
from core.config.settings import get_settings
from shared.types import ExecutionStatus
from shared.exceptions import (
    ExecutionError,
    TimeoutError as AgentGuardTimeoutError,
    SSRFError,
)
from core.observability.logging import get_logger

logger = get_logger(__name__)


class HTTPExecutionProvider(IExecutionProvider):
    """
    HTTP execution provider for REST-based agents.
    
    Features:
    - SSRF protection
    - Request/response size limits
    - Timeout enforcement
    - SSL verification
    - Custom headers support
    - Error handling and retry logic
    """

    def __init__(self):
        self.settings = get_settings()
        self.ssrf_protection = get_ssrf_protection()
        
        # Configure HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=self.settings.max_execution_timeout_seconds,
                write=10.0,
                pool=5.0,
            ),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
            ),
            follow_redirects=False,  # Don't follow redirects for security
        )

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Execute agent via HTTP endpoint.
        
        Args:
            request: Execution request
            
        Returns:
            Execution result
            
        Raises:
            ExecutionError: If execution fails
            TimeoutError: If execution exceeds timeout
            SSRFError: If endpoint fails security checks
        """
        start_time = time.time()
        
        try:
            # Validate endpoint URL
            await self.validate_endpoint(request.endpoint_url)
            
            # Validate request size
            self._validate_request_size(request.input_data)
            
            # Prepare headers
            headers = self._prepare_headers(request)
            
            # Determine timeout
            timeout = min(
                request.context.timeout_seconds,
                self.settings.max_execution_timeout_seconds,
            )
            
            logger.info(
                f"Executing HTTP request to {request.endpoint_url}",
                extra={
                    "execution_id": str(request.context.execution_id),
                    "agent_id": str(request.context.agent_id),
                    "timeout": timeout,
                },
            )
            
            # Execute HTTP request
            try:
                response = await self.client.post(
                    request.endpoint_url,
                    json=request.input_data,
                    headers=headers,
                    timeout=timeout,
                )
            except httpx.TimeoutException:
                duration = time.time() - start_time
                raise AgentGuardTimeoutError(
                    f"HTTP request to {request.endpoint_url}",
                    int(duration),
                )
            except httpx.ConnectError as e:
                raise ExecutionError(
                    f"Failed to connect to {request.endpoint_url}: {str(e)}",
                    details={"endpoint": request.endpoint_url},
                )
            except httpx.RequestError as e:
                raise ExecutionError(
                    f"HTTP request failed: {str(e)}",
                    details={"endpoint": request.endpoint_url},
                )
            
            # Validate response size
            self._validate_response_size(response)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Handle response
            if response.is_success:
                # Parse JSON response
                try:
                    output_data = response.json()
                except Exception as e:
                    logger.warning(
                        f"Failed to parse JSON response: {e}",
                        extra={"execution_id": str(request.context.execution_id)},
                    )
                    output_data = {"raw_response": response.text}
                
                logger.info(
                    f"HTTP execution completed successfully",
                    extra={
                        "execution_id": str(request.context.execution_id),
                        "duration": duration,
                        "status_code": response.status_code,
                    },
                )
                
                return ExecutionResult(
                    execution_id=request.context.execution_id,
                    status=ExecutionStatus.COMPLETED,
                    output_data=output_data,
                    duration_seconds=duration,
                    metadata={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                    },
                )
            else:
                # Handle error response
                error_message = f"HTTP {response.status_code}: {response.text}"
                
                logger.error(
                    f"HTTP execution failed",
                    extra={
                        "execution_id": str(request.context.execution_id),
                        "status_code": response.status_code,
                        "error": response.text[:500],
                    },
                )
                
                return ExecutionResult(
                    execution_id=request.context.execution_id,
                    status=ExecutionStatus.FAILED,
                    error_message=error_message,
                    error_code=f"HTTP_{response.status_code}",
                    duration_seconds=duration,
                    metadata={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                    },
                )
        
        except (ExecutionError, AgentGuardTimeoutError, SSRFError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            # Catch unexpected errors
            duration = time.time() - start_time
            logger.exception(
                f"Unexpected error during execution",
                extra={"execution_id": str(request.context.execution_id)},
            )
            
            return ExecutionResult(
                execution_id=request.context.execution_id,
                status=ExecutionStatus.FAILED,
                error_message=f"Unexpected error: {str(e)}",
                error_code="INTERNAL_ERROR",
                duration_seconds=duration,
            )

    async def validate_endpoint(self, endpoint_url: str) -> bool:
        """
        Validate endpoint URL for SSRF protection.
        
        Args:
            endpoint_url: URL to validate
            
        Returns:
            True if valid
            
        Raises:
            SSRFError: If endpoint fails security checks
        """
        self.ssrf_protection.validate_url(endpoint_url)
        return True

    def supports_mode(self, execution_mode: str) -> bool:
        """Check if provider supports execution mode."""
        return execution_mode.lower() == "http"

    def _prepare_headers(self, request: ExecutionRequest) -> dict:
        """Prepare HTTP headers for request."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"AgentGuard/{self.settings.app_version}",
            "X-Execution-ID": str(request.context.execution_id),
            "X-Agent-ID": str(request.context.agent_id),
        }
        
        # Add correlation ID if present
        if request.context.correlation_id:
            headers["X-Correlation-ID"] = request.context.correlation_id
        
        # Merge custom headers
        if request.headers:
            headers.update(request.headers)
        
        return headers

    def _validate_request_size(self, data: dict) -> None:
        """
        Validate request data size.
        
        Args:
            data: Request data
            
        Raises:
            ExecutionError: If data exceeds size limit
        """
        # Estimate JSON size
        import json
        try:
            json_str = json.dumps(data)
            size_bytes = len(json_str.encode('utf-8'))
            
            if size_bytes > self.settings.max_request_size_bytes:
                raise ExecutionError(
                    f"Request size ({size_bytes} bytes) exceeds limit "
                    f"({self.settings.max_request_size_bytes} bytes)",
                    details={"size_bytes": size_bytes},
                )
        except (TypeError, ValueError) as e:
            raise ExecutionError(f"Failed to serialize request data: {str(e)}")

    def _validate_response_size(self, response: httpx.Response) -> None:
        """
        Validate response size.
        
        Args:
            response: HTTP response
            
        Raises:
            ExecutionError: If response exceeds size limit
        """
        content_length = response.headers.get("content-length")
        
        if content_length:
            size_bytes = int(content_length)
            if size_bytes > self.settings.max_response_size_bytes:
                raise ExecutionError(
                    f"Response size ({size_bytes} bytes) exceeds limit "
                    f"({self.settings.max_response_size_bytes} bytes)",
                    details={"size_bytes": size_bytes},
                )
        
        # Also check actual content size
        actual_size = len(response.content)
        if actual_size > self.settings.max_response_size_bytes:
            raise ExecutionError(
                f"Response size ({actual_size} bytes) exceeds limit "
                f"({self.settings.max_response_size_bytes} bytes)",
                details={"size_bytes": actual_size},
            )

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


# Global instance
_http_provider: Optional[HTTPExecutionProvider] = None


def get_http_provider() -> HTTPExecutionProvider:
    """Get global HTTP execution provider instance."""
    global _http_provider
    if _http_provider is None:
        _http_provider = HTTPExecutionProvider()
    return _http_provider


async def reset_http_provider() -> None:
    """Reset HTTP provider (useful for testing)."""
    global _http_provider
    if _http_provider:
        await _http_provider.close()
    _http_provider = None
