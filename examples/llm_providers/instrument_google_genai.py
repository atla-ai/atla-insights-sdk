"""Google GenAI example."""

import os

from google import genai

from atla_insights import configure, instrument, instrument_google_genai


@instrument("My GenAI application")
def my_app() -> None:
    """My application."""
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Explain how AI works in a few words",
    )


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument Google GenAI
    instrument_google_genai()

    # Calling the instrumented function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
