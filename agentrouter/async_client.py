"""AgentRouter Asynchronous Client."""

import asyncio
import json
import os
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Union, AsyncIterator

from .types import MessageResponse, ContentBlock, ModelInfo
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
from .client import DEFAULT_BASE_URL, DEFAULT_USER_AGENT, DEFAULT_MODEL


class AsyncMessagesResource:
    """Async namespace for message operations."""

    def __init__(self, client: "AsyncAgentRouter"):
        self._client = client

    async def create(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> MessageResponse:
        """Create a message asynchronously."""
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
        if extra_body:
            body.update(extra_body)

        resp_data = await self._client._request("POST", "/v1/messages", body=body)
        return MessageResponse.from_dict(resp_data)

    async def stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """Stream message tokens asynchronously."""
        model = model or self._client.default_model

        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if system is not None:
            body["system"] = system
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if temperature is not None:
            body["temperature"] = temperature
        if extra_body:
            body.update(extra_body)

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        done = object()

        def _worker():
            req = self._client._build_request("POST", "/v1/messages", body=body)
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
                                delta = data_json.get("delta", {})
                                if isinstance(delta, dict) and "text" in delta:
                                    loop.call_soon_threadsafe(queue.put_nowait, delta["text"])
                                elif data_json.get("type") == "content_block_delta":
                                    txt = data_json.get("delta", {}).get("text", "")
                                    if txt:
                                        loop.call_soon_threadsafe(queue.put_nowait, txt)
                                elif "choices" in data_json:
                                    txt = data_json["choices"][0].get("delta", {}).get("content", "")
                                    if txt:
                                        loop.call_soon_threadsafe(queue.put_nowait, txt)
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, e)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, done)

        threading_task = loop.run_in_executor(None, _worker)

        try:
            while True:
                item = await queue.get()
                if item is done:
                    break
                if isinstance(item, Exception):
                    raise item
                yield item
        finally:
            await threading_task


class AsyncModelsResource:
    """Async namespace for model operations."""

    def __init__(self, client: "AsyncAgentRouter"):
        self._client = client

    async def raw(self) -> Dict[str, Any]:
        """Fetch raw JSON from /v1/models."""
        return await self._client._request("GET", "/v1/models")

    async def list(self) -> List[ModelInfo]:
        """Fetch all available models and their full metadata."""
        try:
            data = await self.raw()
            raw_list = data.get("data", [])
            return [ModelInfo.from_dict(m) for m in raw_list]
        except Exception:
            from .models_service import DEFAULT_MODELS
            return [ModelInfo(id=m) for m in DEFAULT_MODELS]

    async def get(self, model_id: str) -> Optional[ModelInfo]:
        """Retrieve details for a specific model ID."""
        models = await self.list()
        for m in models:
            if m.id.lower() == model_id.lower():
                return m
        return None

    async def ids(self) -> List[str]:
        """Fetch list of model IDs as plain strings."""
        models = await self.list()
        return [m.id for m in models]

    async def is_available(self, model_id: str) -> bool:
        """Check if a specific model ID is in the available model list."""
        models = await self.list()
        return any(m.id.lower() == model_id.lower() for m in models)


class AsyncAgentRouter:
    """Asynchronous client for AgentRouter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        default_model: str = DEFAULT_MODEL,
        timeout: float = 60.0,
        max_retries: int = 2,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.api_key = api_key or os.environ.get("AGENTROUTER_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "No API key provided. Pass api_key to AsyncAgentRouter() or set AGENTROUTER_API_KEY environment variable."
            )

        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent

        self.messages = AsyncMessagesResource(self)
        self.models = AsyncModelsResource(self)

    async def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Async high-level helper: returns string response."""
        res = await self.messages.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return res.text

    async def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """Async streaming helper: yields text chunks."""
        async for chunk in self.messages.stream(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        ):
            yield chunk

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

    async def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        for attempt in range(self.max_retries + 1):
            req = self._build_request(method, path, body)

            def _execute():
                try:
                    with urllib.request.urlopen(req, timeout=self.timeout) as response:
                        raw_bytes = response.read()
                        return json.loads(raw_bytes.decode("utf-8")), None
                except urllib.error.HTTPError as e:
                    return None, e
                except urllib.error.URLError as e:
                    return None, e
                except json.JSONDecodeError as e:
                    return None, AgentRouterError(f"Failed to parse server response as JSON: {e}")

            data, err = await asyncio.to_thread(_execute)
            if err is None:
                return data

            if isinstance(err, urllib.error.HTTPError):
                if err.code in {429, 502, 503, 504} and attempt < self.max_retries:
                    await asyncio.sleep(1.0 * (2 ** attempt))
                    continue
                self._handle_http_error(err)
            elif isinstance(err, urllib.error.URLError):
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0 * (2 ** attempt))
                    continue
                raise APIConnectionError(f"Network connection failed: {err.reason}")
            elif isinstance(err, Exception):
                raise err

        raise AgentRouterError("Max retries exceeded without successful response")

    def _handle_http_error(self, e: urllib.error.HTTPError) -> None:
        try:
            err_data = json.loads(e.read().decode("utf-8", errors="replace"))
            msg = err_data.get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)

        if e.code == 401:
            raise AuthenticationError(f"Authentication failed: {msg}.", status_code=401)
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
