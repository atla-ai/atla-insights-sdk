"""Bedrock example."""

import json
import os

import boto3

from atla_insights import (
    configure,
    instrument,
    instrument_bedrock,
)


@instrument("My GenAI application")
def my_app() -> None:
    """My application."""
    bedrock = boto3.client(service_name="bedrock-runtime")
    body = json.dumps(
        {
            "max_tokens": 256,
            "messages": [{"role": "user", "content": "Hello, world"}],
            "anthropic_version": "bedrock-2023-05-31",
        }
    )

    bedrock.invoke_model(body=body, modelId="us.anthropic.claude-3-5-haiku-20241022-v1:0")


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument Bedrock
    instrument_bedrock()

    # Calling the instrumented function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
