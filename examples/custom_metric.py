"""Setting a custom metric example."""

import os

from openai import OpenAI

from atla_insights import (
    configure,
    instrument,
    instrument_openai,
    set_custom_metrics,
)


@instrument("My GenAI application")
def my_app(client: OpenAI) -> None:
    """My application."""
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What is 1 + 2? Reply with only the answer, nothing else.",
            }
        ],
    )

    # Set a custom metric for the correctness of the result
    is_correct = bool(result.choices[0].message.content == "3")
    set_custom_metrics({"correctness": {"data_type": "boolean", "value": is_correct}})


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Create an OpenAI client
    client = OpenAI()

    # Instrument the OpenAI client
    instrument_openai()

    # Calling the instrumented OpenAI client will create spans behind the scenes
    my_app(client)


if __name__ == "__main__":
    main()
