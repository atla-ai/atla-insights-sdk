"""Instrument the deprecated Google GenerativeAI client."""

import os

from google.generativeai.generative_models import GenerativeModel

from atla_insights import configure, instrument
from atla_insights.llm_providers import instrument_google_generativeai


@instrument("My GenAI application")
def my_app() -> None:
    """My application."""
    client = GenerativeModel(model_name="gemini-2.0-flash")
    result = client.generate_content(
        contents="Explain how AI works in a few words",
        stream=True,
    )
    for chunk in result:
        print(chunk)


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument the deprecated Google GenerativeAI library
    instrument_google_generativeai()

    # Calling the instrumented function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
