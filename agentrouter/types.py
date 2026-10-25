"""Data structures and types for AgentRouter responses."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ContentBlock:
    """Represents a content block inside a message response."""
    type: str
    text: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentBlock":
        return cls(
            type=data.get("type", "text"),
            text=data.get("text", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "text": self.text}


@dataclass
class Usage:
    """Token usage details."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Usage":
        if not data:
            return cls()
        inp = data.get("input_tokens", 0) or 0
        out = data.get("output_tokens", 0) or 0
        return cls(
            input_tokens=inp,
            output_tokens=out,
            cache_creation_input_tokens=data.get("cache_creation_input_tokens", 0) or 0,
            cache_read_input_tokens=data.get("cache_read_input_tokens", 0) or 0,
            total_tokens=inp + out
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "total_tokens": self.total_tokens
        }


@dataclass
class MessageResponse:
    """Represents a complete message response returned by AgentRouter."""
    id: str
    model: str
    role: str
    content: List[ContentBlock]
    stop_reason: Optional[str] = None
    usage: Usage = field(default_factory=Usage)
    raw_response: Dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Convenience property to extract combined text content."""
        return "".join(c.text for c in self.content if c.type == "text")

    def __str__(self) -> str:
        return self.text

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageResponse":
        raw_content = data.get("content", [])
        content_blocks = [
            ContentBlock.from_dict(b) if isinstance(b, dict) else ContentBlock(type="text", text=str(b))
            for b in raw_content
        ]
        return cls(
            id=data.get("id", ""),
            model=data.get("model", ""),
            role=data.get("role", "assistant"),
            content=content_blocks,
            stop_reason=data.get("stop_reason"),
            usage=Usage.from_dict(data.get("usage")),
            raw_response=data
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "model": self.model,
            "role": self.role,
            "content": [b.to_dict() for b in self.content],
            "stop_reason": self.stop_reason,
            "usage": self.usage.to_dict(),
            "text": self.text
        }


@dataclass
class ModelInfo:
    """Detailed information about an available model on AgentRouter."""
    id: str
    object: str = "model"
    created: Optional[int] = None
    owned_by: Optional[str] = None
    supported_endpoint_types: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def supported_endpoints(self) -> List[str]:
        """Alias for supported_endpoint_types."""
        return self.supported_endpoint_types

    @property
    def created_at(self) -> Optional[str]:
        """Human-readable UTC date/time string if created timestamp is present."""
        if not self.created:
            return None
        import datetime
        return datetime.datetime.fromtimestamp(self.created, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        return cls(
            id=data.get("id", ""),
            object=data.get("object", "model"),
            created=data.get("created"),
            owned_by=data.get("owned_by"),
            supported_endpoint_types=data.get("supported_endpoint_types", []),
            raw=data,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "created_at": self.created_at,
            "owned_by": self.owned_by,
            "supported_endpoint_types": self.supported_endpoint_types,
        }

    def __str__(self) -> str:
        endpoints = ", ".join(self.supported_endpoint_types) or "none"
        return f"Model(id='{self.id}', owned_by='{self.owned_by}', created={self.created}, endpoints=[{endpoints}])"
