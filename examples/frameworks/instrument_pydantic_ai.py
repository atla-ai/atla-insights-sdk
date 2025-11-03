"""Pydantic AI example."""

import os

from pydantic_ai import Agent

from atla_insights import configure, instrument, instrument_pydantic_ai


@instrument("My Pydantic AI application")
def my_app() -> None:
    """My application."""
    agent = Agent(
        model="openai:gpt-4o",
        name="Hello world agent",
        instructions="You are a helpful agent.",
    )

    return agent.run_sync("hello world")


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument the Pydantic AI
    instrument_pydantic_ai()

    # Calling the instrumented function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
