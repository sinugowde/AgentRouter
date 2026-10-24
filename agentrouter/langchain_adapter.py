"""LangChain integration for AgentRouter.

Enables drop-in usage of AgentRouter inside LangChain, LangGraph, and LCEL pipelines.
"""

from typing import Any, List, Optional, Dict, Iterator
from .client import AgentRouter, DEFAULT_MODEL, DEFAULT_BASE_URL, DEFAULT_USER_AGENT

try:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import (
        BaseMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
        ChatMessage,
    )
    from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
    from langchain_core.callbacks import CallbackManagerForLLMRun
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    BaseChatModel = object  # type: ignore


class ChatAgentRouter(BaseChatModel if _LANGCHAIN_AVAILABLE else object):
    """LangChain Chat Model implementation for AgentRouter.

    Example:
        ```python
        from agentrouter.langchain_adapter import ChatAgentRouter
        from langchain_core.prompts import ChatPromptTemplate

        llm = ChatAgentRouter(model="gpt-6.1-sol")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a concise financial analyst."),
            ("user", "{question}")
        ])
        chain = prompt | llm
        response = chain.invoke({"question": "What is EV/EBITDA?"})
        print(response.content)
        ```
    """

    model_name: str = DEFAULT_MODEL
    api_key: Optional[str] = None
    base_url: str = DEFAULT_BASE_URL
    user_agent: str = DEFAULT_USER_AGENT
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: float = 60.0

    def __init__(self, **kwargs):
        if not _LANGCHAIN_AVAILABLE:
            raise ImportError(
                "langchain_core is required to use ChatAgentRouter. "
                "Install it via: pip install langchain-core"
            )
        super().__init__(**kwargs)

    @property
    def _llm_type(self) -> str:
        return "agentrouter-chat"

    def _get_client(self) -> AgentRouter:
        return AgentRouter(
            api_key=self.api_key,
            base_url=self.base_url,
            default_model=self.model_name,
            timeout=self.timeout,
            user_agent=self.user_agent,
        )

    def _convert_messages(self, messages: List[BaseMessage]) -> tuple[Optional[str], List[Dict[str, str]]]:
        system_prompt: Optional[str] = None
        formatted_messages: List[Dict[str, str]] = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                if system_prompt:
                    system_prompt += "\n" + str(msg.content)
                else:
                    system_prompt = str(msg.content)
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": str(msg.content)})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": str(msg.content)})
            elif isinstance(msg, ChatMessage):
                formatted_messages.append({"role": msg.role, "content": str(msg.content)})
            else:
                formatted_messages.append({"role": "user", "content": str(msg.content)})

        return system_prompt, formatted_messages

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        client = self._get_client()
        system_prompt, formatted_messages = self._convert_messages(messages)

        model = kwargs.get("model", self.model_name)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        response = client.messages.create(
            messages=formatted_messages,
            model=model,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        ai_message = AIMessage(
            content=response.text,
            response_metadata={
                "id": response.id,
                "model": response.model,
                "stop_reason": response.stop_reason,
                "usage": response.usage.to_dict(),
            },
        )
        generation = ChatGeneration(message=ai_message)
        return ChatResult(generations=[generation])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        client = self._get_client()
        system_prompt, formatted_messages = self._convert_messages(messages)

        model = kwargs.get("model", self.model_name)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        for chunk_text in client.messages.stream(
            messages=formatted_messages,
            model=model,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            chunk = ChatGenerationChunk(message=AIMessage(content=chunk_text))
            if run_manager:
                run_manager.on_llm_new_token(chunk_text)
            yield chunk
