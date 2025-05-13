"""Nested instrumentation example."""

import os

from openai import OpenAI

from atla_insights import configure, instrument, instrument_openai


@instrument("My GenAI application")
def my_app(client: OpenAI) -> None:
    """My application."""
    client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Create an OpenAI client
    client = OpenAI()

    # Instrument the OpenAI client
    instrument_openai(client, "my-agent")

    # Calling the instrumented OpenAI client will create spans behind the scenes
    my_app(client)


if __name__ == "__main__":
    main()
