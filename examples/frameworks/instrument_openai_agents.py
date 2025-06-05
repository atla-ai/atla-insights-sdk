"""OpenAI Agents SDK example."""

import asyncio
import os

from agents import Agent, Runner

from atla_insights import configure, instrument, instrument_openai_agents


@instrument("My OpenAI Agents application")
async def my_async_app() -> None:
    """My application."""
    agent = Agent(name="Hello world", instructions="You are a helpful agent.")
    await Runner.run(agent, "Hello world")


async def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument the OpenAI Agents SDK
    instrument_openai_agents()

    # Calling the instrumented function will create spans behind the scenes
    await my_async_app()


if __name__ == "__main__":
    asyncio.run(main())
