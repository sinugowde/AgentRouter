"""Quickstart Example: Basic chat with AgentRouter."""

import os
from agentrouter import AgentRouter

# 1. Initialize client (reads AGENTROUTER_API_KEY from environment, or pass directly)
api_key = os.environ.get("AGENTROUTER_API_KEY", "sk-***")
client = AgentRouter(api_key=api_key)

# 2. Simple one-liner query with default model (gpt-6.1-sol)
print("=== 1. Simple Prompt with gpt-6.1-sol ===")
reply = client.chat("Explain quantum computing in one sentence.")
print(reply)

# 3. Query with gpt-6-astra
print("\n=== 2. Prompt with gpt-6-astra ===")
reply_astra = client.chat("What are three key principles of clean code?", model="gpt-6-astra")
print(reply_astra)

# 4. List available models
print("\n=== 3. Available Models ===")
models = client.models.list()
for m in models:
    print(f"- {m.id}")
