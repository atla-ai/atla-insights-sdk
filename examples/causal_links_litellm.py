"""Causal-link example using LiteLLM.

Run with:

    export ATLA_INSIGHTS_TOKEN="<your token>"
    python examples/causal_links_litellm.py

This demonstrates how to declare that the second LLM call is causally linked to
the first one using the ``link_from`` context-manager.  We use LiteLLM with
``mock_response`` so no real API key / network request is needed.
"""

from __future__ import annotations

import os
from typing import Any

from litellm import completion

from atla_insights import (
    configure,
    instrument,
    instrument_litellm,
    link_from,
)

# ---------------------------------------------------------------------------
# Agent A
# ---------------------------------------------------------------------------


@instrument("Agent A - initial question", capture_span=True)
def call_agent_a(question: str) -> Any:
    """First LLM call that produces an answer."""
    # Make a LiteLLM completion (instrumented automatically by atla-insights).
    response = completion(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
        mock_response="42",
    )

    return response["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Agent B
# ---------------------------------------------------------------------------


@instrument("Agent B - follow-up", capture_span=True)
def call_agent_b(text: str) -> Any:
    """Second LLM call that uses Agent A's answer."""
    response = completion(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Summarise: {text}"}],
        mock_response="The answer is 42.",
    )

    return response["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


@instrument("main")
def main() -> None:  # noqa: D103
    # Step 1: Agent A answers the question.
    answer, span_a = call_agent_a("What is the meaning of life?")

    # Step 2: Agent B is called; we declare causal linkage.
    with link_from(span_a):
        summary, span_b = call_agent_b(answer)

    print("Answer:", answer)
    print("Summary:", summary)
    from opentelemetry.trace import format_span_id

    print("Span A ID:", format_span_id(span_a.get_span_context().span_id))
    print("Span B ID:", format_span_id(span_b.get_span_context().span_id))


if __name__ == "__main__":
    # Configure Atla Insights
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Enable LiteLLM auto-instrumentation.
    instrument_litellm()
    main()
