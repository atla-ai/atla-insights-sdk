"""Test the CrewAI instrumentation."""

import pytest
from crewai import LLM, Agent, Crew, Task
from openai import OpenAI

from tests._otel import BaseLocalOtel


class TestCrewAIInstrumentation(BaseLocalOtel):
    """Test the CrewAI instrumentation."""

    def test_basic(self, mock_openai_client: OpenAI) -> None:
        """Test basic CrewAI instrumentation."""
        from src.atla_insights import instrument_crewai

        with instrument_crewai():
            test_agent = Agent(
                role="test",
                goal="test",
                backstory="test",
                llm=LLM(
                    model="openai/some-model",
                    api_base=str(mock_openai_client.base_url),
                    api_key="unit-test",
                ),
            )
            test_task = Task(description="test", expected_output="test", agent=test_agent)
            test_crew = Crew(agents=[test_agent], tasks=[test_task])
            test_crew.kickoff()

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3

        kickoff, execute, request = finished_spans

        assert kickoff.name == "Crew.kickoff"
        assert execute.name == "Task._execute_core"
        assert request.name == "litellm_request"

        assert request.attributes is not None
        assert request.attributes.get("gen_ai.prompt.0.role") == "system"
        assert request.attributes.get("gen_ai.prompt.0.content") is not None
        assert request.attributes.get("gen_ai.prompt.1.role") == "user"
        assert request.attributes.get("gen_ai.prompt.1.content") is not None
        assert request.attributes.get("gen_ai.completion.0.role") == "assistant"
        assert request.attributes.get("gen_ai.completion.0.content") == "hello world"

    @pytest.mark.asyncio
    async def test_async(self, mock_openai_client: OpenAI) -> None:
        """Test basic async CrewAI instrumentation."""
        from src.atla_insights import instrument_crewai

        with instrument_crewai():
            test_agent = Agent(
                role="test",
                goal="test",
                backstory="test",
                llm=LLM(
                    model="openai/some-model",
                    api_base=str(mock_openai_client.base_url),
                    api_key="unit-test",
                ),
            )
            test_task = Task(description="test", expected_output="test", agent=test_agent)
            test_crew = Crew(agents=[test_agent], tasks=[test_task])
            await test_crew.kickoff_async()

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3

        kickoff, execute, request = finished_spans

        assert kickoff.name == "Crew.kickoff"
        assert execute.name == "Task._execute_core"
        assert request.name == "litellm_request"

        assert request.attributes is not None
        assert request.attributes.get("gen_ai.prompt.0.role") == "system"
        assert request.attributes.get("gen_ai.prompt.0.content") is not None
        assert request.attributes.get("gen_ai.prompt.1.role") == "user"
        assert request.attributes.get("gen_ai.prompt.1.content") is not None
        assert request.attributes.get("gen_ai.completion.0.role") == "assistant"
        assert request.attributes.get("gen_ai.completion.0.content") == "hello world"

    def test_ctx(self, mock_openai_client: OpenAI) -> None:
        """Test that the CrewAI instrumentation is traced."""
        from src.atla_insights import instrument_crewai

        with instrument_crewai():
            test_agent = Agent(
                role="test",
                goal="test",
                backstory="test",
                llm=LLM(
                    model="openai/some-model",
                    api_base=str(mock_openai_client.base_url),
                    api_key="unit-test",
                ),
            )
            test_task = Task(description="test", expected_output="test", agent=test_agent)
            test_crew = Crew(agents=[test_agent], tasks=[test_task])
            test_crew.kickoff()

        # This extra call is not instrumented
        test_crew.kickoff()

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3

        kickoff, execute, request = finished_spans

        assert kickoff.name == "Crew.kickoff"
        assert execute.name == "Task._execute_core"
        assert request.name == "litellm_request"
