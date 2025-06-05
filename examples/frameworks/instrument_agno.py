"""Agno example."""

import os

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from atla_insights import configure, instrument, instrument_agno


@instrument("My Agno application")
def my_app() -> None:
    """My application."""
    agent = Agent(model=OpenAIChat(id="gpt-4o-mini"))
    agent.run("Hello world!")


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument Agno with OpenAI
    instrument_agno("openai")

    # Calling the instrumented function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
