"""Streaming Example: Real-time token streaming with AgentRouter."""

import os
from agentrouter import AgentRouter

api_key = os.environ.get("AGENTROUTER_API_KEY", "sk-***")
client = AgentRouter(api_key=api_key)

print("Streaming response in real-time:\n")
for chunk in client.stream("Write a short haiku about coding.", model="gpt-6-astra"):
    print(chunk, end="", flush=True)
print("\n")
