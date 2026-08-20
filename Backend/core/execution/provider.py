"""
Execution Provider Contract.

Defines the interface for executing agents across different modes (HTTP, SDK, browser, etc.).
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from shared.types import ExecutionStatus


class ExecutionContext(BaseModel):
    """Context for an execution request."""
    execution_id: UUID
    agent_id: UUID
    agent_version_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    correlation_id: Optional[str] = None
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = {}


class ExecutionRequest(BaseModel):
    """Request to execute an agent."""
    context: ExecutionContext
    endpoint_url: str
    input_data: Dict[str, Any]
    headers: Optional[Dict[str, str]] = None


class ExecutionResult(BaseModel):
    """Result of an agent execution."""
    execution_id: UUID
    status: ExecutionStatus
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = {}


class IExecutionProvider(ABC):
    """
    Interface for execution providers.
    
    Different implementations can support different execution modes:
    - HTTPExecutionProvider: Execute via HTTP/REST endpoints
    - SDKExecutionProvider: Execute using language-specific SDKs
    - BrowserExecutionProvider: Execute browser-based agents
    - DockerExecutionProvider: Execute in isolated containers
    """

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Execute an agent.
        
        Args:
            request: Execution request with context and input
            
        Returns:
            Execution result with output or error
            
        Raises:
            ExecutionError: If execution fails
            TimeoutError: If execution exceeds timeout
            SecurityError: If security checks fail
        """
        pass

    @abstractmethod
    async def validate_endpoint(self, endpoint_url: str) -> bool:
        """
        Validate that an endpoint is safe to execute.
        
        Args:
            endpoint_url: URL to validate
            
        Returns:
            True if endpoint is safe, False otherwise
            
        Raises:
            SSRFError: If endpoint fails security checks
        """
        pass

    @abstractmethod
    def supports_mode(self, execution_mode: str) -> bool:
        """
        Check if provider supports a given execution mode.
        
        Args:
            execution_mode: Execution mode (http, sdk, browser, etc.)
            
        Returns:
            True if mode is supported
        """
        pass
