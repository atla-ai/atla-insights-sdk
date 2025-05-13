"""Nested instrumentation example."""

import os

from openai import OpenAI

from atla_insights import (
    configure,
    instrument,
    instrument_openai,
    mark_failure,
    mark_success,
)


@instrument("My GenAI application")
def my_app(client: OpenAI) -> None:
    """My application."""
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What is 1 + 2? Reply with only the answer, nothing else.",
            }
        ],
    )

    # Check whether the result meets some expected success criteria
    # In this example, we use a simple string match.
    if result.choices[0].message.content == "3":
        mark_success()
    else:
        mark_failure()


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Create an OpenAI client
    client = OpenAI()

    # Instrument the OpenAI client
    instrument_openai(client)

    # Calling the instrumented OpenAI client will create spans behind the scenes
    my_app(client)


if __name__ == "__main__":
    main()
