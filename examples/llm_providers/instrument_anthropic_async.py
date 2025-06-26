"""Async Anthropic example."""

import asyncio
import os

from anthropic import AsyncAnthropic

from atla_insights import configure, instrument, instrument_anthropic


@instrument("My GenAI application")
async def my_async_app(client: AsyncAnthropic) -> None:
    """My async application."""
    await client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello, Claude"}],
    )


async def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Create an async Anthropic client
    client = AsyncAnthropic()

    # Instrument Anthropic
    instrument_anthropic()

    # Calling the instrumented async Anthropic client will create spans behind the scenes
    await my_async_app(client)


if __name__ == "__main__":
    asyncio.run(main())
