"""Test the CrewAI instrumentation."""

import pytest
from crewai import LLM, Agent, Crew, Task
from crewai.tools.tool_usage import CrewStructuredTool, ToolCalling, ToolUsage
from openai import OpenAI

from tests._otel import BaseLocalOtel


class TestCrewAIInstrumentation(BaseLocalOtel):
    """Test the CrewAI instrumentation."""

    def test_basic(self, mock_openai_client: OpenAI) -> None:
        """Test basic CrewAI instrumentation."""
        from atla_insights import instrument_crewai

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

        assert len(finished_spans) == 5

        kickoff, crew_create, execute, task_create, request = finished_spans

        assert kickoff.name == "Crew.kickoff"
        assert crew_create.name == "Crew Created"
        assert execute.name == "Task._execute_core"
        assert task_create.name == "Task Created"
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
        from atla_insights import instrument_crewai

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

        assert len(finished_spans) == 5

        kickoff, crew_create, execute, task_create, request = finished_spans

        assert kickoff.name == "Crew.kickoff"
        assert crew_create.name == "Crew Created"
        assert execute.name == "Task._execute_core"
        assert task_create.name == "Task Created"
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
        from atla_insights import instrument_crewai

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

        assert len(finished_spans) == 7

        kickoff, crew_create, execute, task_create, request, _, _ = finished_spans

        assert kickoff.name == "Crew.kickoff"
        assert crew_create.name == "Crew Created"
        assert execute.name == "Task._execute_core"
        assert task_create.name == "Task Created"
        assert request.name == "litellm_request"

    def test_tool_invocation(self) -> None:
        """Test the CrewAI instrumentation with tool invocation."""
        from atla_insights import instrument_crewai

        with instrument_crewai():

            def test_function(some_arg: str) -> str:
                """Test function."""
                return "some-result"

            tool = CrewStructuredTool.from_function(func=test_function)
            tool_usage = ToolUsage(
                tools_handler=None,
                tools=[tool],
                task=None,
                function_calling_llm=None,
            )
            tool_calling = ToolCalling(
                tool_name="test_function",
                arguments={"some_arg": "some-value"},
            )
            tool_usage._use("test_function", tool, tool_calling)

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2

        span, tool_usage_span = finished_spans

        assert span.name == "test_function"
        assert tool_usage_span.name == "Tool Usage"

        assert span.attributes is not None
        assert span.attributes.get("openinference.span.kind") == "TOOL"

        assert span.attributes.get("tool.name") == "test_function"
        assert span.attributes.get("tool.description") == "Test function."
        assert span.attributes.get("tool.parameters") == '{"some_arg": "some-value"}'

        assert span.attributes.get("input.value") is not None
        assert span.attributes.get("output.value") == "some-result"

    def test_multi_agent_crew(self, mock_openai_client: OpenAI) -> None:
        """Test CrewAI with multiple agents collaborating."""
        from atla_insights import instrument_crewai

        with instrument_crewai():
            agent1 = Agent(
                role="researcher",
                goal="research topics",
                backstory="expert researcher",
                llm=LLM(
                    model="openai/some-model",
                    api_base=str(mock_openai_client.base_url),
                    api_key="unit-test",
                ),
            )
            agent2 = Agent(
                role="writer",
                goal="write content",
                backstory="expert writer",
                llm=LLM(
                    model="openai/some-model",
                    api_base=str(mock_openai_client.base_url),
                    api_key="unit-test",
                ),
            )

            task1 = Task(description="research", expected_output="report", agent=agent1)
            task2 = Task(description="write", expected_output="article", agent=agent2)

            crew = Crew(agents=[agent1, agent2], tasks=[task1, task2])
            crew.kickoff()

        finished_spans = self.get_finished_spans()

        # Kickoff, crew creation, 2 task executions, 2 task creations, 2 llm requests
        assert len(finished_spans) == 8

        span_names = [span.name for span in finished_spans]
        assert "Crew.kickoff" in span_names
        assert "Crew Created" in span_names
        assert span_names.count("Task._execute_core") == 2
        assert span_names.count("Task Created") == 2

    def test_kickoff_for_each(self, mock_openai_client: OpenAI) -> None:
        """Test CrewAI kickoff_for_each for batch processing."""
        from atla_insights import instrument_crewai

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

            inputs = [{"topic": "foo"}, {"topic": "bar"}]
            test_crew.kickoff_for_each(inputs=inputs)

        finished_spans = self.get_finished_spans()

        # One crew kickoff per input
        kickoff_spans = [span for span in finished_spans if span.name == "Crew.kickoff"]
        assert len(kickoff_spans) >= 2
