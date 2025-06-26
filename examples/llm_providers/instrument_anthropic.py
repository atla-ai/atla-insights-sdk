"""Anthropic example."""

import os

from anthropic import Anthropic

from atla_insights import configure, instrument, instrument_anthropic


@instrument("My GenAI application")
def my_app() -> None:
    """My application."""
    client = Anthropic()
    client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello, Claude"}],
    )


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument Anthropic
    instrument_anthropic()

    # Calling the instrumented function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
