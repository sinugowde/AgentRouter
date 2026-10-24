"""Multi-turn Conversation Example: Context retention across multiple turns."""

import os
from agentrouter import AgentRouter

api_key = os.environ.get("AGENTROUTER_API_KEY", "sk-***")
client = AgentRouter(api_key=api_key)

chat = client.conversation(
    model="gpt-6-astra",
    system="You are an expert equity research analyst. Be concise."
)

print("Turn 1:")
r1 = chat.send("What are the key moat factors for semiconductor foundry businesses?")
print(r1.text)

print("\nTurn 2 (Follow-up using context):")
r2 = chat.send("Which specific company best illustrates these factors?")
print(r2.text)
