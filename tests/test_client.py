"""Unit tests for AgentRouter client."""

import unittest
from unittest.mock import patch, MagicMock
import json
import io

from agentrouter import (
    AgentRouter,
    AuthenticationError,
    RateLimitError,
    BadRequestError,
    MessageResponse,
    ContentBlock,
    Usage,
)
from agentrouter.models_service import DEFAULT_MODELS


class TestAgentRouterTypes(unittest.TestCase):
    def test_message_response_parsing(self):
        data = {
            "id": "msg-123",
            "model": "gpt-6.1-sol",
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hello world!"}
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5
            }
        }
        res = MessageResponse.from_dict(data)
        self.assertEqual(res.id, "msg-123")
        self.assertEqual(res.model, "gpt-6.1-sol")
        self.assertEqual(res.text, "Hello world!")
        self.assertEqual(str(res), "Hello world!")
        self.assertEqual(res.usage.input_tokens, 10)
        self.assertEqual(res.usage.output_tokens, 5)
        self.assertEqual(res.usage.total_tokens, 15)

    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(AuthenticationError):
                AgentRouter(api_key=None)


class TestAgentRouterMockedCalls(unittest.TestCase):
    def setUp(self):
        self.client = AgentRouter(api_key="sk-test-mock-key")

    @patch("urllib.request.urlopen")
    def test_chat_helper(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "id": "chat-1",
            "model": "gpt-6.1-sol",
            "content": [{"type": "text", "text": "Mock response"}]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        text = self.client.chat("Hello?")
        self.assertEqual(text, "Mock response")

    @patch("urllib.request.urlopen")
    def test_conversation_history(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "id": "chat-2",
            "model": "gpt-6.1-sol",
            "content": [{"type": "text", "text": "Answer 1"}]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        chat = self.client.conversation(model="gpt-6.1-sol")
        resp = chat.send("Hello")
        self.assertEqual(resp.text, "Answer 1")
        self.assertEqual(len(chat.history), 2)
        self.assertEqual(chat.history[0], {"role": "user", "content": "Hello"})
        self.assertEqual(chat.history[1], {"role": "assistant", "content": "Answer 1"})

        chat.clear()
        self.assertEqual(len(chat.history), 0)


if __name__ == "__main__":
    unittest.main()
