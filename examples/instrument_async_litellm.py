"""Nested instrumentation example."""

import asyncio
import os

from litellm import acompletion

from atla_insights import configure, instrument, instrument_litellm


@instrument("My GenAI application")
async def my_async_app() -> None:
    """My async application."""
    await acompletion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello, world!"}],
        mock_response="Hello, world!",
    )


async def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument liteLLM
    instrument_litellm()

    # Calling the instrumented liteLLM function will create spans behind the scenes
    await my_async_app()

    # NOTE: litellm callbacks are invoked asynchronously, leading to a race condition
    # with program termination. This is open issue in litellm.
    await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
