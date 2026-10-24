# AgentRouter Client Library

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero-Dependency Core](https://img.shields.io/badge/dependencies-zero%20(stdlib)-brightgreen.svg)]()

A lightweight, high-performance client library for [AgentRouter](https://agentrouter.org/). Enables seamless access to AgentRouter's next-gen models (**`gpt-6.1-sol`**, **`gpt-6-astra`**, **`gpt-5.6-sol`**) across your Python and Node.js projects.

---

## Key Insights & Protocol Specification

AgentRouter exposes an **Anthropic-compatible Messages protocol** at `/v1/messages`.

> [!IMPORTANT]
> **Gateway Requirement**: AgentRouter's API gateway strictly mandates the header:
> ```http
> User-Agent: claude-cli/2.0.0 (external, cli)
> ```
> Without this exact header, the server rejects requests with `401 Unauthorized`. This library handles all required headers and protocol nuances automatically.

### Supported Models
- **`gpt-6.1-sol`** (Default) - High-capability reasoning and general tasks
- **`gpt-6-astra`** - Fast, concise generation and conversational tasks
- **`gpt-5.6-sol`** - Lightweight, high-throughput model

---

## Installation

### Option 1: Install from Local Clone
```bash
# Clone the repository and enter the directory
git clone https://github.com/sinugowde/AgentRouter.git
cd AgentRouter

# Standard install
pip install .

# Or editable / development mode
pip install -e .

# With optional extras (e.g. LangChain, Anthropic SDK):
pip install ".[langchain]"
pip install ".[anthropic]"
pip install ".[all]"
```

### Option 2: Install Directly via Git
Install straight into any project or virtual environment without manually cloning first:
```bash
pip install git+https://github.com/sinugowde/AgentRouter.git

# With extras:
pip install "agentrouter[langchain] @ git+https://github.com/sinugowde/AgentRouter.git"
```

### Option 3: Reference from Another Local Project
If working locally across multiple projects without publishing to PyPI:
```bash
# Install as editable from your other project's folder:
pip install -e /path/to/AgentRouter
```

---

## Configuration

Set your API key as an environment variable (recommended) or pass it directly in code:

### PowerShell
```powershell
$env:AGENTROUTER_API_KEY="sk-***"
```

### Linux / macOS / Bash
```bash
export AGENTROUTER_API_KEY="sk-***"
```

---

## Python Usage Guide

### 1. Simple One-Liner Chat
```python
from agentrouter import AgentRouter

client = AgentRouter()  # Automatically reads AGENTROUTER_API_KEY

# Quick prompt with default model (gpt-6.1-sol)
response = client.chat("What is the capital of France?")
print(response)

# Switch to gpt-6-astra
astra_reply = client.chat("Summarize cloud computing in 10 words.", model="gpt-6-astra")
print(astra_reply)
```

### 2. Real-Time Streaming
```python
from agentrouter import AgentRouter

client = AgentRouter()

for chunk in client.stream("Explain machine learning in simple terms", model="gpt-6.1-sol"):
    print(chunk, end="", flush=True)
print()
```

### 3. Multi-Turn Conversation (Automatic History)
```python
from agentrouter import AgentRouter

client = AgentRouter()
chat = client.conversation(
    model="gpt-6-astra",
    system="You are an expert equity research analyst. Be concise."
)

# Turn 1
r1 = chat.send("What are the primary revenue drivers for Nvidia?")
print("Assistant:", r1.text)

# Turn 2 (automatically retains context from Turn 1!)
r2 = chat.send("How does their data center segment compare to gaming?")
print("Assistant:", r2.text)
```

### 4. Advanced Messages API (`messages.create`)
```python
from agentrouter import AgentRouter

client = AgentRouter()

response = client.messages.create(
    model="gpt-6.1-sol",
    system="You are an assistant that outputs strictly JSON.",
    messages=[
        {"role": "user", "content": "Return a JSON object with 'status' and 'timestamp'"}
    ],
    temperature=0.2,
    max_tokens=200
)

print("ID:", response.id)
print("Content:", response.text)
print("Token Usage:", response.usage)
```

### 5. Asynchronous Client (`AsyncAgentRouter`)
Ideal for FastAPI, async background workers, or LangGraph:
```python
import asyncio
from agentrouter import AsyncAgentRouter

async def main():
    client = AsyncAgentRouter()
    
    # Async chat
    reply = await client.chat("Hello async world!")
    print(reply)
    
    # Async streaming
    async for token in client.stream("Count to 3"):
        print(token, end="", flush=True)

asyncio.run(main())
```

---

## LangChain & LangGraph Integration

A first-class `ChatAgentRouter` class is included:

```python
from agentrouter.langchain_adapter import ChatAgentRouter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Initialize LangChain model
llm = ChatAgentRouter(model="gpt-6-astra", temperature=0.5)

# 2. Build LCEL Pipeline
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise financial tutor."),
    ("user", "Explain: {term}")
])

chain = prompt | llm | StrOutputParser()

# 3. Invoke
result = chain.invoke({"term": "EBITDA"})
print(result)
```

---

## Anthropic Official SDK Bridge

If your existing codebase uses the official `anthropic` SDK:

```python
from agentrouter import AgentRouter

# Option A: Helper factory
client = AgentRouter()
anthropic_client = client.anthropic_client()

# Option B: Direct standard Anthropic instantiation
import anthropic
anthropic_client = anthropic.Anthropic(
    api_key="sk-***",
    base_url="https://agentrouter.org",
    default_headers={"User-Agent": "claude-cli/2.0.0 (external, cli)"}
)

message = anthropic_client.messages.create(
    model="gpt-6.1-sol",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello via Anthropic SDK!"}]
)
print(message.content[0].text)
```

---

## Command-Line Interface (CLI)

Run single prompts, list models, or enter interactive chat directly from your terminal:

```bash
# Single prompt
python -m agentrouter "Who created Linux?" --model gpt-6-astra

# Interactive chat shell
python -m agentrouter -i --model gpt-6.1-sol

# List available models
python -m agentrouter --list-models
```

---

## JavaScript / Node.js Client (`js/`)

Zero dependencies (uses native `fetch` in Node 18+ and modern browsers):

```javascript
import AgentRouter from "./js/index.js";

const client = new AgentRouter({
  apiKey: process.env.AGENTROUTER_API_KEY
});

// 1. One-liner chat
const reply = await client.chat("Explain P/E ratio.", { model: "gpt-6-astra" });
console.log(reply);

// 2. Real-time streaming
for await (const chunk of client.stream("Tell me a joke")) {
  process.stdout.write(chunk);
}

// 3. Multi-turn conversation
const chat = client.conversation({ model: "gpt-6.1-sol" });
await chat.send("My name is Alex.");
const followUp = await chat.send("What is my name?");
console.log(followUp.text);
```

---

## Resilience & Auto-Retry

AgentRouter may occasionally return `502 Bad Gateway` or `429 Rate Limit` when upstream providers undergo transient load.

Both `AgentRouter` and `AsyncAgentRouter` include **automatic exponential backoff retries** (default: `max_retries=2`) on HTTP `429`, `502`, `503`, and `504` status codes, ensuring that your scripts don't fail during brief upstream spikes.

---

## Project Structure

```
AgentRouter/
├── agentrouter/
│   ├── __init__.py           # Exports & version
│   ├── client.py             # Sync AgentRouter client & MessagesResource
│   ├── async_client.py       # AsyncAgentRouter client
│   ├── conversation.py       # Multi-turn history manager
│   ├── models_service.py     # Model discovery (/v1/models)
│   ├── langchain_adapter.py  # ChatAgentRouter (BaseChatModel)
│   ├── types.py              # MessageResponse, Usage, ContentBlock
│   ├── exceptions.py         # Custom exception hierarchy
│   ├── cli.py                # Terminal CLI implementation
│   └── __main__.py           # Entrypoint for python -m agentrouter
├── js/
│   ├── index.js              # Native Node.js/ESM client
│   ├── index.d.ts            # TypeScript definitions
│   ├── example.js            # Node.js example script
│   └── package.json          # npm package definition
├── examples/
│   ├── 01_quickstart.py
│   ├── 02_streaming.py
│   ├── 03_multi_turn_chat.py
│   ├── 04_langchain_example.py
│   └── 05_anthropic_sdk_bridge.py
├── tests/
│   └── test_client.py        # Automated unit tests
├── .env.example              # Environment variables template
├── pyproject.toml            # Modern pip install packaging
├── setup.py                  # Traditional setuptools configuration
└── README.md                 # Full documentation
```
