"""Models service for listing and querying AgentRouter supported models."""

from typing import List, Optional
from .types import ModelInfo
from .exceptions import AgentRouterError

# Known tested default models supported by AgentRouter
DEFAULT_MODELS = [
    "gpt-6.1-sol",
    "gpt-6-astra",
    "gpt-5.6-sol"
]


class ModelsService:
    def __init__(self, client):
        self._client = client

    def list(self) -> List[ModelInfo]:
        """Fetch list of available models from AgentRouter API."""
        try:
            data = self._client._request("GET", "/v1/models")
            raw_list = data.get("data", [])
            return [ModelInfo.from_dict(m) for m in raw_list]
        except Exception:
            # Fallback to known list if models endpoint is temporarily unavailable
            return [ModelInfo(id=m) for m in DEFAULT_MODELS]

    def ids(self) -> List[str]:
        """Fetch list of model IDs as plain strings."""
        return [m.id for m in self.list()]

    def is_available(self, model_id: str) -> bool:
        """Check if a specific model ID is in the available model list."""
        return model_id in self.ids()
