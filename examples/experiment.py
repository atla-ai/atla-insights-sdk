"""Running an experiment example."""

import os

from openai import OpenAI

from atla_insights import (
    configure,
    instrument,
    instrument_openai,
    run_experiment,
)


@instrument("My GenAI application")
def my_app(client: OpenAI) -> None:
    """My application."""
    _ = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What is 1 + 2? Reply with only the answer, nothing else.",
            }
        ],
    )


def main() -> None:
    """Main function."""
    # Configure the client. Experiments run in the "dev" environment by default,
    # but setting this here avoids a warning.
    configure(
        token=os.environ["ATLA_INSIGHTS_TOKEN"],
        environment="dev",
    )

    # Create an OpenAI client
    client = OpenAI()

    # Instrument the OpenAI client
    instrument_openai()

    # Run your app in the context of an experiment.
    # Your traces with be associated with a new run for the experiment.
    with run_experiment(experiment_id="123"):
        my_app(client)


if __name__ == "__main__":
    main()
