"""Test the CrewAI instrumentation."""

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

        assert len(finished_spans) == 5

        kickoff, crew, execute, task_create, request = finished_spans

        assert kickoff.name == "Crew.kickoff"
        assert crew.name == "Crew Created"
        assert execute.name == "Task._execute_core"
        assert task_create.name == "Task Created"
        assert request.name == "litellm_request"
