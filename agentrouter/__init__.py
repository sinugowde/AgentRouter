"""
AgentRouter - Python client library for https://agentrouter.org/

Provides zero-dependency access to AgentRouter LLMs (gpt-6.1-sol, gpt-6-astra, gpt-5.6-sol),
with streaming support, multi-turn conversations, Anthropic SDK compatibility bridge,
and LangChain / LangGraph integration.
"""

from .client import AgentRouter, DEFAULT_BASE_URL, DEFAULT_USER_AGENT, DEFAULT_MODEL
from .async_client import AsyncAgentRouter
from .conversation import Conversation
from .types import MessageResponse, ContentBlock, Usage, ModelInfo
from .exceptions import (
    AgentRouterError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    RateLimitError,
    BadRequestError,
    InternalServerError,
    APIConnectionError,
)

# Optional LangChain adapter
try:
    from .langchain_adapter import ChatAgentRouter
except Exception:
    ChatAgentRouter = None  # type: ignore

__version__ = "0.1.0"

__all__ = [
    "AgentRouter",
    "AsyncAgentRouter",
    "Conversation",
    "MessageResponse",
    "ContentBlock",
    "Usage",
    "ModelInfo",
    "ChatAgentRouter",
    "AgentRouterError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "RateLimitError",
    "BadRequestError",
    "InternalServerError",
    "APIConnectionError",
    "DEFAULT_BASE_URL",
    "DEFAULT_USER_AGENT",
    "DEFAULT_MODEL",
    "__version__",
]
