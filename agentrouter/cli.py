"""Command-line interface for AgentRouter."""

import argparse
import os
import sys
from .client import AgentRouter, DEFAULT_MODEL
from .exceptions import AgentRouterError


def main():
    parser = argparse.ArgumentParser(
        description="AgentRouter CLI - Query LLMs via AgentRouter API",
        prog="agentrouter",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Prompt to send to the model (omit for interactive mode)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL}). e.g. gpt-6.1-sol, gpt-6-astra",
    )
    parser.add_argument(
        "-s",
        "--system",
        default=None,
        help="System instruction / prompt",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Launch interactive multi-turn chat session",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models supported by your subscription",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="AgentRouter API Key (overrides AGENTROUTER_API_KEY environment variable)",
    )

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("AGENTROUTER_API_KEY")
    if not api_key:
        print("Error: No API key provided.", file=sys.stderr)
        print("Set the AGENTROUTER_API_KEY environment variable or pass --api-key <key>", file=sys.stderr)
        sys.exit(1)

    try:
        client = AgentRouter(api_key=api_key)

        if args.list_models:
            print(f"Fetching available models from {client.base_url}...")
            models = client.models.list()
            print("\nAvailable Models:")
            for m in models:
                print(f"  - {m.id}")
            return

        if args.interactive or not args.prompt:
            print(f"AgentRouter Interactive Shell (Model: {args.model})")
            print("Type 'exit' or 'quit' to end session. Type 'clear' to reset history.\n")
            chat = client.conversation(model=args.model, system=args.system)
            while True:
                try:
                    user_input = input("\nYou > ").strip()
                    if not user_input:
                        continue
                    if user_input.lower() in ("exit", "quit"):
                        print("Goodbye!")
                        break
                    if user_input.lower() == "clear":
                        chat.clear()
                        print("[Conversation history cleared]")
                        continue

                    print(f"\n{args.model} > ", end="", flush=True)
                    for chunk in chat.stream(user_input):
                        print(chunk, end="", flush=True)
                    print()
                except (KeyboardInterrupt, EOFError):
                    print("\nSession ended.")
                    break
            return

        # Single prompt execution
        if args.no_stream:
            answer = client.chat(args.prompt, model=args.model, system=args.system)
            print(answer)
        else:
            for chunk in client.stream(args.prompt, model=args.model, system=args.system):
                print(chunk, end="", flush=True)
            print()

    except AgentRouterError as e:
        print(f"\n[AgentRouter Error] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[Unexpected Error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
