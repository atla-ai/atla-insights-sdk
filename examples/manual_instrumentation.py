"""This example shows how to instrument a custom service with Atla Insights."""

import os

from atla_insights import configure, instrument
from atla_insights.span import start_as_current_span


@instrument("My GenAI application")
def my_app() -> None:
    """My application."""
    with start_as_current_span("my-llm-generation") as span:
        span.record_generation(
            input_messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"},
            ],
            output_messages=[
                {"role": "assistant", "content": "The capital of France is Paris."},
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "get_capital",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "country": {"type": "string"},
                            },
                            "required": ["country"],
                        },
                    },
                },
            ],
        )


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Calling the instrumented function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
