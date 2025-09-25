"""Google ADK example."""

import asyncio
import os

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from atla_insights import configure, instrument, instrument_google_adk


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    return {
        "status": "success",
        "report": (f"The weather in {city} is sunny with a temperature of 25 degrees."),
    }


@instrument("My GenAI application")
async def my_app() -> None:
    """My ADK application."""
    my_agent = LlmAgent(
        name="my_agent",
        model="gemini-2.0-flash",
        description=("Agent to answer questions about the weather in a city."),
        instruction=("You are an agent who can answer user questions about the weather."),
        tools=[get_weather],
    )

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="my_app",
        user_id="user_1",
        session_id="session_1",
    )

    runner = Runner(
        agent=my_agent,
        app_name="my_app",
        session_service=session_service,
    )

    async for event in runner.run_async(
        user_id="user_1",
        session_id="session_1",
        new_message=types.Content(
            role="user", parts=[types.Part(text="What is the weather in Tokyo?")]
        ),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(event.content.parts[0].text)


async def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument Google ADK
    instrument_google_adk()

    # Invoking the instrumented ADK application will create spans behind the scenes
    await my_app()


if __name__ == "__main__":
    asyncio.run(main())
