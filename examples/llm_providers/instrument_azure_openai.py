"""AzureOpenAI example."""

import os

from openai import AzureOpenAI

from atla_insights import configure, instrument, instrument_openai


@instrument("My GenAI application")
def my_app(client: AzureOpenAI) -> None:
    """My application."""
    client.chat.completions.create(
        model="my-azure-deployment",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Create an AzureOpenAI client
    client = AzureOpenAI(
        azure_endpoint="https://my-endpoint.openai.azure.com/",
        api_version="2024-02-15-preview",
    )

    # Instrument OpenAI (incl. AzureOpenAI)
    instrument_openai()

    # Calling the instrumented AzureOpenAI client will create spans behind the scenes
    my_app(client)


if __name__ == "__main__":
    main()
