"""HuggingFace Smolagents example."""

import os

from smolagents import CodeAgent, LiteLLMModel, WebSearchTool

from atla_insights import configure, instrument, instrument_smolagents


@instrument("My Smolagents application")
def my_app() -> None:
    """My application."""
    model = LiteLLMModel(model_id="gpt-4o-mini")
    agent = CodeAgent(model=model, tools=[WebSearchTool()], stream_outputs=True)

    agent.run(
        "How many seconds would it take for a leopard at full speed to run through "
        "Pont des Arts?"
    )


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument the Smolagents framework with a LiteLLM LLM provider
    instrument_smolagents("litellm")

    # Calling the instrumented function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
