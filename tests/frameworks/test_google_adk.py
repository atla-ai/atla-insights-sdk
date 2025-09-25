"""Test the CrewAI instrumentation."""

import pytest
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import Client, types
from openai import OpenAI

from tests._otel import BaseLocalOtel


def some_tool(some_arg: str) -> dict:
    """Some tool."""
    return {
        "status": "success",
        "report": "Some result.",
    }


class TestGoogleADKInstrumentation(BaseLocalOtel):
    """Test the Google ADK instrumentation."""

    def setup_method(self) -> None:
        """Setup the method."""
        self.session_service = InMemorySessionService()

    @pytest.mark.asyncio
    async def test_basic(self, mock_google_genai_client: Client) -> None:
        """Test basic Google ADK instrumentation with Gemini."""
        from atla_insights import instrument_google_adk

        # Set Gemini client to mock client to avoid actual API calls
        model = Gemini(model="some-model")
        model.api_client = mock_google_genai_client

        # Set up state config
        agent_name = "test_agent"
        app_name = "test"
        user_id = "test_user"
        session_id = "test_session"

        with instrument_google_adk():
            test_agent = LlmAgent(
                name=agent_name,
                model=model,
                description=("Agent to answer questions about the weather in a city."),
                instruction=(
                    "You are an agent who can answer user questions about the weather."
                ),
                tools=[some_tool],
            )
            await self.session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
            test_runner = Runner(
                agent=test_agent,
                app_name=app_name,
                session_service=self.session_service,
            )

            async for _ in test_runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part(text="foo")]),
            ):
                pass

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3

        invocation, run, llm_call = finished_spans

        assert invocation.name == f"invocation [{app_name}]"
        assert run.name == f"agent_run [{agent_name}]"
        assert llm_call.name == "call_llm"

        assert llm_call.attributes is not None
        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "system"
        assert llm_call.attributes.get("llm.input_messages.0.message.content") is not None
        assert llm_call.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call.attributes.get(
                "llm.input_messages.1.message.contents.0.message_content.text"
            )
            == "foo"
        )

        assert (
            llm_call.attributes.get("llm.tools.0.tool.json_schema")
            == '{"description":"Some tool.","name":"some_tool","parameters":{"properties":{"some_arg":{"type":"STRING"}},"required":["some_arg"],"type":"OBJECT"}}'  # noqa: E501
        )

        assert llm_call.attributes.get("llm.output_messages.0.message.role") == "model"
        assert (
            llm_call.attributes.get(
                "llm.output_messages.0.message.contents.0.message_content.text"
            )
            == "hello world"
        )

    @pytest.mark.asyncio
    async def test_litellm(self, mock_openai_client: OpenAI) -> None:
        """Test basic Google ADK instrumentation with LiteLLM."""
        from atla_insights import instrument_google_adk

        # Set LiteLLM client to mock client to avoid actual API calls
        model = LiteLlm(
            model="openai/some-model",
            api_base=str(mock_openai_client.base_url),
            api_key="unit-test",
        )

        # Set up state config
        agent_name = "test_agent"
        app_name = "test"
        user_id = "test_user"
        session_id = "test_session"

        with instrument_google_adk():
            test_agent = LlmAgent(
                name=agent_name,
                model=model,
                description=("Agent to answer questions about the weather in a city."),
                instruction=(
                    "You are an agent who can answer user questions about the weather."
                ),
                tools=[some_tool],
            )
            await self.session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
            test_runner = Runner(
                agent=test_agent,
                app_name=app_name,
                session_service=self.session_service,
            )

            async for _ in test_runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part(text="foo")]),
            ):
                pass

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3

        invocation, run, llm_call = finished_spans

        assert invocation.name == f"invocation [{app_name}]"
        assert run.name == f"agent_run [{agent_name}]"
        assert llm_call.name == "call_llm"

        assert llm_call.attributes is not None
        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "system"
        assert llm_call.attributes.get("llm.input_messages.0.message.content") is not None
        assert llm_call.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call.attributes.get(
                "llm.input_messages.1.message.contents.0.message_content.text"
            )
            == "foo"
        )

        assert (
            llm_call.attributes.get("llm.tools.0.tool.json_schema")
            == '{"description":"Some tool.","name":"some_tool","parameters":{"properties":{"some_arg":{"type":"STRING"}},"required":["some_arg"],"type":"OBJECT"}}'  # noqa: E501
        )

        assert llm_call.attributes.get("llm.output_messages.0.message.role") == "model"
        assert (
            llm_call.attributes.get(
                "llm.output_messages.0.message.contents.0.message_content.text"
            )
            == "hello world"
        )
