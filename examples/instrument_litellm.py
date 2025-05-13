"""Nested instrumentation example."""

import os

from litellm import completion

from atla_insights import configure, instrument, instrument_litellm


@instrument("My GenAI application")
def my_app() -> None:
    """My application."""
    completion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello, world!"}],
        mock_response="Hello, world!",
    )


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument liteLLM
    instrument_litellm()

    # Calling the instrumented liteLLM function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
