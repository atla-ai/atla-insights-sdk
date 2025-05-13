"""Nested instrumentation example."""

import asyncio
import os

from openai import AsyncOpenAI

from atla_insights import configure, instrument, instrument_openai


@instrument("My GenAI application")
async def my_async_app(client: AsyncOpenAI) -> None:
    """My async application."""
    await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )


async def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Create an async OpenAI client
    client = AsyncOpenAI()

    # Instrument the async OpenAI client
    instrument_openai(client)

    # Calling the instrumented async OpenAI client will create spans behind the scenes
    await my_async_app(client)


if __name__ == "__main__":
    asyncio.run(main())
