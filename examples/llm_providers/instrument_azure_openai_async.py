"""AzureOpenAI example."""

import asyncio
import os

from openai import AsyncAzureOpenAI

from atla_insights import configure, instrument, instrument_openai


@instrument("My GenAI application")
async def my_app(client: AsyncAzureOpenAI) -> None:
    """My application."""
    await client.chat.completions.create(
        model="my-azure-deployment",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )


async def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Create an AsyncAzureOpenAI client
    client = AsyncAzureOpenAI(
        azure_endpoint="https://my-endpoint.openai.azure.com/",
        api_version="2024-02-15-preview",
    )

    # Instrument OpenAI (incl. AsyncAzureOpenAI)
    instrument_openai()

    # Calling the instrumented AsyncAzureOpenAI client will create spans behind the scenes
    await my_app(client)


if __name__ == "__main__":
    asyncio.run(main())
