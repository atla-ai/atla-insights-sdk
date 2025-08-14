"""Example of interacting with traces using the data API client."""

import os

from atla_insights import Client


def main() -> None:
    """Main function."""
    # Configure the API client.
    client = Client(api_key=os.environ["ATLA_INSIGHTS_TOKEN"])
    print(client)

    # # Instrument the Smolagents framework with a LiteLLM LLM provider
    # instrument_smolagents("litellm")

    # # Calling the instrumented function will create spans behind the scenes
    # my_app()


if __name__ == "__main__":
    main()
