"""ElevenLabs example."""

import os
import signal

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

from atla_insights import configure, instrument, instrument_elevenlabs


@instrument("My GenAI application")
def my_app(conversation: Conversation) -> None:
    """My application."""
    conversation.start_session()

    signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())

    conversation_id = conversation.wait_for_session_end()
    print(f"Conversation ID: {conversation_id}")


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument ElevenLabs
    instrument_elevenlabs()

    # Set up ElevenLabs conversation
    agent_id = os.getenv("AGENT_ID")
    api_key = os.getenv("ELEVENLABS_API_KEY")

    elevenlabs = ElevenLabs(api_key=api_key)

    conversation = Conversation(
        elevenlabs,
        agent_id,
        requires_auth=bool(api_key),
        audio_interface=DefaultAudioInterface(),
        # Simple callbacks that print the conversation to the console.
        callback_agent_response=lambda response: print(f"Agent: {response}"),
        callback_agent_response_correction=lambda original, corrected: print(
            f"Agent: {original} -> {corrected}"
        ),
        callback_user_transcript=lambda transcript: print(f"User: {transcript}"),
    )

    # Calling the instrumented function will create spans behind the scenes
    my_app(conversation)


if __name__ == "__main__":
    main()
