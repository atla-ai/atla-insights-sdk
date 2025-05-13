"""Example of adding metadata to a run."""

import os

from litellm import completion

from atla_insights import configure, instrument, instrument_litellm


@instrument("My GenAI application")
def my_app() -> None:
    """My application."""
    completion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello, world!"}],
        mock_response="Hello, world!",
    )


def main() -> None:
    """Main function."""
    # Define metadata I want to attach to the run
    metadata = {
        "environment": "sbx",
        "prompt-version": "v1.3",
        "run-name": "my-experiment",
    }

    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"], metadata=metadata)

    # Instrument liteLLM
    instrument_litellm()

    # Calling the instrumented liteLLM function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
