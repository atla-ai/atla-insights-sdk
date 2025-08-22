"""Running an experiment example."""

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
    # Configure the client
    configure(token="pylf_v1_eu_GWQ3C6xppx3CWfgvnsTgXmz5TRdPYdTfqHl6dtynlZVv")
    # configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Create an OpenAI client
    client = OpenAI()

    # Instrument the OpenAI client
    instrument_openai()

    # Run your app in the context of an experiment.
    # Your traces with be associated with a new run for the experiment.
    with run_experiment("My experiment"):
        my_app(client)


if __name__ == "__main__":
    main()
