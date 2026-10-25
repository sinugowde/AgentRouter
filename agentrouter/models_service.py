"""Models service for querying and inspecting AgentRouter supported models."""

from typing import List, Optional, Dict, Any
from .types import ModelInfo

# Known tested default models supported by AgentRouter
DEFAULT_MODELS = [
    "gpt-6.1-sol",
    "gpt-6-astra",
    "gpt-5.6-sol"
]


class ModelsService:
    """Service to discover, list, and retrieve details for available models."""

    def __init__(self, client):
        self._client = client

    def raw(self) -> Dict[str, Any]:
        """
        Fetch the raw JSON response from GET /v1/models.

        Returns:
            Dict containing {"data": [...], "success": True}
        """
        return self._client._request("GET", "/v1/models")

    def list(self) -> List[ModelInfo]:
        """
        Fetch all available models and their full metadata (id, created, owned_by, supported_endpoint_types).

        Returns:
            List of ModelInfo objects.
        """
        try:
            data = self.raw()
            raw_list = data.get("data", [])
            return [ModelInfo.from_dict(m) for m in raw_list]
        except Exception:
            # Fallback to known list if models endpoint is temporarily unavailable
            return [ModelInfo(id=m) for m in DEFAULT_MODELS]

    def get(self, model_id: str) -> Optional[ModelInfo]:
        """
        Retrieve details for a specific model ID.

        Args:
            model_id: Name/ID of the model (e.g. 'gpt-6.1-sol', 'gpt-6-astra')

        Returns:
            ModelInfo instance if found, or None.
        """
        for model in self.list():
            if model.id.lower() == model_id.lower():
                return model
        return None

    def ids(self) -> List[str]:
        """
        Fetch list of model IDs as plain strings.

        Returns:
            List of strings, e.g. ['gpt-5.6-sol', 'gpt-6-astra', 'gpt-6.1-sol']
        """
        return [m.id for m in self.list()]

    def is_available(self, model_id: str) -> bool:
        """
        Check if a specific model ID is in the available model list.

        Args:
            model_id: Name/ID of the model

        Returns:
            bool: True if available, False otherwise.
        """
        return any(m.id.lower() == model_id.lower() for m in self.list())
