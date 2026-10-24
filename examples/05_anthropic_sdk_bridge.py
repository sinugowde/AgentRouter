"""Anthropic Official SDK Bridge Example:
Using AgentRouter directly through the official `anthropic` Python SDK.
"""

import os
from agentrouter import AgentRouter

api_key = os.environ.get("AGENTROUTER_API_KEY", "sk-***")

# 1. Use the built-in bridge factory
client = AgentRouter(api_key=api_key)
anthropic_client = client.anthropic_client()

# 2. Or create manually with standard anthropic package:
# import anthropic
# anthropic_client = anthropic.Anthropic(
#     api_key=api_key,
#     base_url="https://agentrouter.org",
#     default_headers={"User-Agent": "claude-cli/2.0.0 (external, cli)"}
# )

print("Calling AgentRouter via Anthropic SDK...")
message = anthropic_client.messages.create(
    model="gpt-6-astra",
    max_tokens=150,
    messages=[
        {"role": "user", "content": "Explain compound interest in 1 sentence."}
    ]
)

print("\nResponse from Anthropic SDK:")
print(message.content[0].text)
print("\nUsage:", message.usage)
