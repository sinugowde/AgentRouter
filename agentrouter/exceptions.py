"""AgentRouter Exceptions."""

from typing import Optional, Any


class AgentRouterError(Exception):
    """Base exception for all AgentRouter errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(AgentRouterError):
    """Raised when authentication fails (HTTP 401). Check your API key."""
    pass


class PermissionDeniedError(AgentRouterError):
    """Raised when access is forbidden (HTTP 403)."""
    pass


class NotFoundError(AgentRouterError):
    """Raised when a resource or model is not found (HTTP 404)."""
    pass


class RateLimitError(AgentRouterError):
    """Raised when rate limit or quota is exceeded (HTTP 429)."""
    pass


class APIConnectionError(AgentRouterError):
    """Raised when network connection fails or times out."""
    pass


class BadRequestError(AgentRouterError):
    """Raised when the server rejects the request format (HTTP 400)."""
    pass


class InternalServerError(AgentRouterError):
    """Raised when the server encounters an internal error (HTTP 500+)."""
    pass
