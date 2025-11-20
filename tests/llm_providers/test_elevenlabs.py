"""Test ElevenLabs instrumentation."""

import asyncio
import time
from typing import Awaitable, Callable

import pytest
from elevenlabs import AsyncElevenLabs, ElevenLabs
from elevenlabs.conversational_ai.conversation import (
    AsyncAudioInterface,
    AsyncConversation,
    AudioInterface,
    Conversation,
)

from tests._otel import BaseLocalOtel


class _StubAudioInterface(AudioInterface):
    """Audio interface stub that avoids pyaudio dependencies."""

    def start(self, input_callback: Callable[[bytes], None]) -> None:
        pass

    def stop(self) -> None:
        pass

    def output(self, audio: bytes) -> None:
        pass

    def interrupt(self) -> None:
        pass


class _StubAsyncAudioInterface(AsyncAudioInterface):
    """Async audio interface stub that avoids pyaudio dependencies."""

    async def start(self, input_callback: Callable[[bytes], Awaitable[None]]) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def output(self, audio: bytes) -> None:
        pass

    async def interrupt(self) -> None:
        pass


@pytest.fixture(scope="function")
def mock_conversation(mock_elevenlabs_client: ElevenLabs) -> Conversation:
    """Mock ElevenLabs Conversation object.

    :param mock_elevenlabs_client (ElevenLabs): Mock ElevenLabs client.
    :return (Conversation): Mock conversation object.
    """
    return Conversation(
        client=mock_elevenlabs_client,
        agent_id="unit-test",
        requires_auth=False,
        audio_interface=_StubAudioInterface(),
    )


@pytest.fixture(scope="function")
def mock_async_conversation(
    mock_async_elevenlabs_client: AsyncElevenLabs,
) -> AsyncConversation:
    """Mock ElevenLabs AsyncConversation object.

    :param mock_elevenlabs_client (AsyncElevenLabs): Mock AsyncElevenLabs client.
    :return (AsyncConversation): Mock async conversation object.
    """
    return AsyncConversation(
        client=mock_async_elevenlabs_client,  # type: ignore
        agent_id="unit-test",
        requires_auth=False,
        audio_interface=_StubAsyncAudioInterface(),
    )


class TestElevenLabsInstrumentation(BaseLocalOtel):
    """Test the ElevenLabs instrumentation."""

    def test_basic(self, mock_conversation: Conversation) -> None:
        """Test basic ElevenLabs instrumentation."""
        from atla_insights import instrument_elevenlabs

        with instrument_elevenlabs():
            mock_conversation.start_session()
            time.sleep(0.1)  # simulate activity
            mock_conversation.end_session()

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None
        assert span.attributes.get("atla.audio.conversation_id") == "unit-test"

    @pytest.mark.asyncio
    async def test_async(self, mock_async_conversation: AsyncConversation) -> None:
        """Test basic async ElevenLabs instrumentation."""
        from atla_insights import instrument_elevenlabs

        with instrument_elevenlabs():
            await mock_async_conversation.start_session()
            await asyncio.sleep(0.1)  # simulate activity
            await mock_async_conversation.end_session()

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None
        assert span.attributes.get("atla.audio.conversation_id") == "unit-test"

    def test_ctx(self, mock_conversation: Conversation) -> None:
        """Test ElevenLabs instrumentation context manager."""
        from atla_insights import instrument_elevenlabs

        with instrument_elevenlabs():
            mock_conversation.start_session()
            time.sleep(0.1)  # simulate activity
            mock_conversation.end_session()

        # This session should not get picked up
        mock_conversation.start_session()
        time.sleep(0.1)  # simulate activity
        mock_conversation.end_session()

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1
