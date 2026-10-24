"""AgentRouter Synchronous Client."""

import json
import os
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Union, Iterator

from .types import MessageResponse, ContentBlock
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
from .models_service import ModelsService
from .conversation import Conversation

DEFAULT_BASE_URL = "https://agentrouter.org"
DEFAULT_USER_AGENT = "claude-cli/2.0.0 (external, cli)"
DEFAULT_MODEL = "gpt-6.1-sol"
DEFAULT_MAX_RETRIES = 2
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


class MessagesResource:
    """Namespace for message-related operations."""

    def __init__(self, client: "AgentRouter"):
        self._client = client

    def create(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> Union[MessageResponse, Iterator[str]]:
        """
        Create a message with AgentRouter.

        Args:
            messages: List of message dicts, e.g. [{"role": "user", "content": "..."}]
            model: Model ID to use (e.g. 'gpt-6.1-sol', 'gpt-6-astra')
            system: Optional system instruction prompt
            max_tokens: Optional maximum tokens to generate
            temperature: Optional sampling temperature
            stream: If True, yields streaming text chunks as an iterator
            extra_body: Optional additional fields to merge into JSON body

        Returns:
            MessageResponse if stream=False, or Iterator[str] yielding text tokens if stream=True
        """
        model = model or self._client.default_model

        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if system is not None:
            body["system"] = system
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if temperature is not None:
            body["temperature"] = temperature
        if stream:
            body["stream"] = True
        if extra_body:
            body.update(extra_body)

        if stream:
            return self._stream_request("/v1/messages", body)

        resp_data = self._client._request("POST", "/v1/messages", body=body)
        return MessageResponse.from_dict(resp_data)

    def stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> Iterator[str]:
        """Convenience method to stream response tokens for given messages."""
        return self.create(
            messages=messages,
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            extra_body=extra_body,
        )

    def _stream_request(self, path: str, body: Dict[str, Any]) -> Iterator[str]:
        """Handles Server-Sent Events (SSE) streaming for messages."""
        req = self._client._build_request("POST", path, body=body)
        try:
            with urllib.request.urlopen(req, timeout=self._client.timeout) as response:
                for line_bytes in response:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or line.startswith("event:"):
                        continue
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            # Handle Anthropic-style delta
                            delta = data_json.get("delta", {})
                            if isinstance(delta, dict) and "text" in delta:
                                yield delta["text"]
                            # Handle direct content block text
                            elif data_json.get("type") == "content_block_delta":
                                delta_text = data_json.get("delta", {}).get("text", "")
                                if delta_text:
                                    yield delta_text
                            # Fallback for OpenAI style delta
                            elif "choices" in data_json:
                                chunk = data_json["choices"][0].get("delta", {}).get("content", "")
                                if chunk:
                                    yield chunk
                        except json.JSONDecodeError:
                            continue
        except urllib.error.HTTPError as e:
            self._client._handle_http_error(e)
        except urllib.error.URLError as e:
            raise APIConnectionError(f"Network connection failed: {e.reason}")


class AgentRouter:
    """
    Main client for interacting with AgentRouter API.

    Usage:
        client = AgentRouter()  # Reads AGENTROUTER_API_KEY from environment
        # or
        client = AgentRouter(api_key="sk-...")

        # Simple 1-liner
        reply = client.chat("Who are you?", model="gpt-6.1-sol")

        # Streaming
        for chunk in client.stream("Tell me a story"):
            print(chunk, end="", flush=True)

        # Multi-turn conversation
        chat = client.conversation()
        chat.send("Hi")
        chat.send("What did I just say?")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        default_model: str = DEFAULT_MODEL,
        timeout: float = 60.0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.api_key = api_key or os.environ.get("AGENTROUTER_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "No API key provided. Pass api_key to AgentRouter() or set AGENTROUTER_API_KEY environment variable."
            )

        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent

        self.messages = MessagesResource(self)
        self.models = ModelsService(self)

    def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        High-level helper: send a prompt and get back the assistant's text string directly.

        Args:
            prompt: User question or prompt string
            model: Model name (defaults to client.default_model, e.g. 'gpt-6.1-sol')
            system: Optional system instruction prompt
            max_tokens: Optional token limit
            temperature: Optional sampling temperature

        Returns:
            The assistant's generated text answer.
        """
        response = self.messages.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.text

    def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[str]:
        """
        High-level helper: stream tokens for a prompt in real time.

        Yields:
            Individual text token strings as they arrive.
        """
        return self.messages.stream(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def conversation(
        self,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Conversation:
        """
        Start a stateful multi-turn conversation that remembers history.
        """
        return Conversation(
            client=self,
            model=model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def anthropic_client(self):
        """
        Returns an official `anthropic.Anthropic` client preconfigured
        to point at AgentRouter with the required user-agent and base_url.

        Requires the `anthropic` package installed (`pip install anthropic`).
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required to use this bridge. Install it with: pip install anthropic"
            )
        return anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers={"User-Agent": self.user_agent},
        )

    def _build_request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> urllib.request.Request:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        return urllib.request.Request(url, data=data, headers=headers, method=method)

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        for attempt in range(self.max_retries + 1):
            req = self._build_request(method, path, body)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    raw_bytes = response.read()
                    return json.loads(raw_bytes.decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    time.sleep(1.0 * (2 ** attempt))
                    continue
                self._handle_http_error(e)
            except urllib.error.URLError as e:
                if attempt < self.max_retries:
                    time.sleep(1.0 * (2 ** attempt))
                    continue
                raise APIConnectionError(f"Network connection failed: {e.reason}")
            except json.JSONDecodeError as e:
                raise AgentRouterError(f"Failed to parse server response as JSON: {e}")
        raise AgentRouterError("Max retries exceeded without successful response")

    def _handle_http_error(self, e: urllib.error.HTTPError) -> None:
        try:
            err_data = json.loads(e.read().decode("utf-8", errors="replace"))
            msg = err_data.get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)

        if e.code == 401:
            raise AuthenticationError(
                f"Authentication failed: {msg}. Ensure your API key is valid and User-Agent is '{self.user_agent}'.",
                status_code=401,
            )
        elif e.code == 403:
            raise PermissionDeniedError(msg, status_code=403)
        elif e.code == 404:
            raise NotFoundError(msg, status_code=404)
        elif e.code == 429:
            raise RateLimitError(msg, status_code=429)
        elif e.code == 400:
            raise BadRequestError(msg, status_code=400)
        elif e.code >= 500:
            raise InternalServerError(msg, status_code=e.code)
        else:
            raise AgentRouterError(msg, status_code=e.code)
