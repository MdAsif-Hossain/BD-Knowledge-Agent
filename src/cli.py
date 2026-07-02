"""Terminal REPL for the Multi-Tool AI Agent.

Run with:  ``python -m src.cli``
"""

from __future__ import annotations

import sys

from src.agent import build_agent

# Bengali names (and other non-ASCII text) can appear in answers; make sure the
# console can print them on Windows (default code page is often cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BANNER = r"""
============================================================
   Multi-Tool AI Agent for Bangladesh
   Ask about institutions, hospitals, restaurants, or
   general knowledge. Type 'exit' or 'quit' to leave.
============================================================
"""

EXAMPLES = [
    "How many hospitals are there in Dhaka?",
    "List some institutions in Rajshahi division.",
    "Which restaurants have the highest ratings?",
    "What is the role of DGHS in Bangladesh?",
]


def main() -> None:
    print(BANNER)
    print("Try, e.g.:")
    for example in EXAMPLES:
        print(f"  - {example}")

    agent = build_agent(verbose=True)

    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not question:
            continue

        try:
            result = agent.invoke({"input": question})
            print(f"\nAgent: {result['output']}")
        except Exception as exc:  # noqa: BLE001
            print(f"\n[error] {exc}")


if __name__ == "__main__":
    main()
