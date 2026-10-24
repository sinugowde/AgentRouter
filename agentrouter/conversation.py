"""Conversation manager for stateful, multi-turn dialogues with AgentRouter."""

from typing import List, Dict, Any, Optional, Iterator
from .types import MessageResponse


class Conversation:
    """Manages chat history and context across multiple turns."""

    def __init__(
        self,
        client,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        self._client = client
        self.model = model or client.default_model
        self.system = system
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._history: List[Dict[str, str]] = []

    @property
    def history(self) -> List[Dict[str, str]]:
        """Return the current message history."""
        return list(self._history)

    def add_user_message(self, content: str) -> None:
        """Manually append a user message to history."""
        self._history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Manually append an assistant message to history."""
        self._history.append({"role": "assistant", "content": content})

    def clear(self) -> None:
        """Reset conversation history."""
        self._history.clear()

    def send(self, prompt: str, **kwargs) -> MessageResponse:
        """Send a new user prompt, append both prompt and response to history, and return the response."""
        self.add_user_message(prompt)

        req_kwargs: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": self._history,
        }
        if self.system or "system" in kwargs:
            req_kwargs["system"] = kwargs.get("system", self.system)
        if self.temperature is not None or "temperature" in kwargs:
            req_kwargs["temperature"] = kwargs.get("temperature", self.temperature)
        if self.max_tokens is not None or "max_tokens" in kwargs:
            req_kwargs["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        response = self._client.messages.create(**req_kwargs)
        self.add_assistant_message(response.text)
        return response

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream response for the prompt, updating history once complete."""
        self.add_user_message(prompt)

        req_kwargs: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": self._history,
        }
        if self.system or "system" in kwargs:
            req_kwargs["system"] = kwargs.get("system", self.system)
        if self.temperature is not None or "temperature" in kwargs:
            req_kwargs["temperature"] = kwargs.get("temperature", self.temperature)
        if self.max_tokens is not None or "max_tokens" in kwargs:
            req_kwargs["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        accumulated = []
        for chunk in self._client.messages.stream(**req_kwargs):
            accumulated.append(chunk)
            yield chunk

        self.add_assistant_message("".join(accumulated))
