"""Test the LangChain instrumentation."""

import json

import pytest
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from openai import OpenAI
from pydantic import SecretStr
from typing_extensions import TypedDict

from tests._otel import BaseLocalOtel


class TestLangChainInstrumentation(BaseLocalOtel):
    """Test the LangChain instrumentation."""

    def test_basic_langchain(self, mock_openai_client: OpenAI) -> None:
        """Test basic Langchain instrumentation."""
        from atla_insights import instrument_langchain

        with instrument_langchain():
            chat = ChatOpenAI(  # type: ignore[call-arg]
                api_key=SecretStr("unit-test"),
                base_url=str(mock_openai_client.base_url),
                model="some-model",
            )

            messages = [HumanMessage(content="Hello, world!")]
            chat.invoke(messages)

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None

        assert span.name == "ChatOpenAI"

        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, world!"
        )

        assert span.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            span.attributes.get("llm.output_messages.0.message.content") == "hello world"
        )

    def test_basic_langgraph(self, mock_openai_client: OpenAI) -> None:
        """Test basic Langgraph instrumentation."""
        from atla_insights import instrument_langchain

        with instrument_langchain():
            chat = ChatOpenAI(  # type: ignore[call-arg]
                api_key=SecretStr("unit-test"),
                base_url=str(mock_openai_client.base_url),
                model="some-model",
            )

            def generate_message(state):
                messages = [HumanMessage(content="Hello, world!")]
                response = chat.invoke(messages)
                state["messages"] = [*messages, response]
                return state

            class TestState(TypedDict):
                messages: list

            workflow = StateGraph(TestState)
            workflow.add_node("generate", generate_message)
            workflow.set_entry_point("generate")
            workflow.add_edge("generate", END)

            app = workflow.compile()
            app.invoke(TestState(messages=[]))  # type: ignore[arg-type]

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "LangGraph"
        assert llm_call.name == "generate"
        assert request.name == "ChatOpenAI"

        assert request.attributes is not None

        assert request.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            request.attributes.get("llm.input_messages.0.message.content")
            == "Hello, world!"
        )

        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    def test_tool_invocation(self) -> None:
        """Test the LangChain instrumentation with tool invocation."""
        from atla_insights import instrument_langchain

        with instrument_langchain():

            @tool
            def test_function(some_arg: str) -> str:
                """Test function."""
                return "some-result"

            test_function.invoke({"some_arg": "some-value"})

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "test_function"

        assert span.attributes is not None
        assert span.attributes.get("openinference.span.kind") == "TOOL"

        assert span.attributes.get("tool.name") == "test_function"
        assert span.attributes.get("tool.description") == "Test function."
        assert span.attributes.get("tool.parameters") == '{"some_arg": "some-value"}'

        assert span.attributes.get("input.value") == "{'some_arg': 'some-value'}"
        assert span.attributes.get("output.value") == "some-result"

    def test_streaming_langchain(self, mock_openai_stream_client: OpenAI) -> None:
        """Test streaming with LangChain."""
        from atla_insights import instrument_langchain

        with instrument_langchain():
            chat = ChatOpenAI(  # type: ignore[call-arg]
                api_key=SecretStr("unit-test"),
                base_url=str(mock_openai_stream_client.base_url),
                model="some-model",
            )

            messages = [HumanMessage(content="Hello, world!")]
            for _ in chat.stream(messages):
                pass

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.name == "ChatOpenAI"
        assert span.attributes is not None
        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, world!"
        )

    @pytest.mark.asyncio
    async def test_async_langchain(self, mock_async_openai_client: OpenAI) -> None:
        """Test async LangChain instrumentation."""
        from atla_insights import instrument_langchain

        with instrument_langchain():
            chat = ChatOpenAI(  # type: ignore[call-arg]
                api_key=SecretStr("unit-test"),
                base_url=str(mock_async_openai_client.base_url),
                model="some-model",
            )

            messages = [HumanMessage(content="Hello, world!")]
            await chat.ainvoke(messages)

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.name == "ChatOpenAI"
        assert span.attributes is not None
        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, world!"
        )
        assert span.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            span.attributes.get("llm.output_messages.0.message.content") == "hello world"
        )

    @pytest.mark.asyncio
    async def test_async_streaming_langchain(
        self, mock_async_openai_stream_client: OpenAI
    ) -> None:
        """Test async streaming with LangChain."""
        from atla_insights import instrument_langchain

        with instrument_langchain():
            chat = ChatOpenAI(  # type: ignore[call-arg]
                api_key=SecretStr("unit-test"),
                base_url=str(mock_async_openai_stream_client.base_url),
                model="some-model",
            )

            messages = [HumanMessage(content="Hello, world!")]
            async for _ in chat.astream(messages):
                pass

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.name == "ChatOpenAI"
        assert span.attributes is not None
        assert span.attributes.get("llm.input_messages.0.message.role") == "user"

    @pytest.mark.asyncio
    async def test_async_langgraph(self, mock_async_openai_client: OpenAI) -> None:
        """Test async LangGraph instrumentation."""
        from atla_insights import instrument_langchain

        with instrument_langchain():
            chat = ChatOpenAI(  # type: ignore[call-arg]
                api_key=SecretStr("unit-test"),
                base_url=str(mock_async_openai_client.base_url),
                model="some-model",
            )

            async def generate_message(state):
                messages = [HumanMessage(content="Hello, world!")]
                response = await chat.ainvoke(messages)
                state["messages"] = [*messages, response]
                return state

            class TestState(TypedDict):
                messages: list

            workflow = StateGraph(TestState)
            workflow.add_node("generate", generate_message)
            workflow.set_entry_point("generate")
            workflow.add_edge("generate", END)

            app = workflow.compile()
            await app.ainvoke(TestState(messages=[]))  # type: ignore[arg-type]

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "LangGraph"
        assert llm_call.name == "generate"
        assert request.name == "ChatOpenAI"

        assert request.attributes is not None
        assert request.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            request.attributes.get("llm.input_messages.0.message.content")
            == "Hello, world!"
        )
        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    def test_context_manager(self, mock_openai_client: OpenAI) -> None:
        """Test that instrumentation only applies within context."""
        from atla_insights import instrument_langchain

        with instrument_langchain():
            chat = ChatOpenAI(  # type: ignore[call-arg]
                api_key=SecretStr("unit-test"),
                base_url=str(mock_openai_client.base_url),
                model="some-model",
            )

            messages = [HumanMessage(content="Hello, world!")]
            chat.invoke(messages)

        # This call should not be instrumented (outside context)
        chat.invoke(messages)

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

    def test_multi_agent(self, mock_openai_client: OpenAI) -> None:
        """Test multi-agent tracking."""
        from atla_insights import instrument_langchain

        with instrument_langchain():
            chat = ChatOpenAI(  # type: ignore[call-arg]
                api_key=SecretStr("unit-test"),
                base_url=str(mock_openai_client.base_url),
                model="some-model",
                metadata={"langgraph_node": "my-agent"},
            )

            messages = [HumanMessage(content="Hello, world!")]
            chat.invoke(messages)

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [llm_call] = finished_spans

        assert llm_call.attributes is not None
        metadata = dict(json.loads(str(llm_call.attributes.get("metadata"))))
        assert metadata.get("langgraph_node") == "my-agent"

    def test_multi_agent_graph(self, mock_openai_client: OpenAI) -> None:
        """Test multi-agent tracking in a graph."""
        from atla_insights import instrument_langchain

        with instrument_langchain():
            chat = ChatOpenAI(  # type: ignore[call-arg]
                api_key=SecretStr("unit-test"),
                base_url=str(mock_openai_client.base_url),
                model="some-model",
            )

            def generate_message(state):
                messages = [HumanMessage(content="Hello, world!")]
                response = chat.invoke(messages)
                state["messages"] = [*messages, response]
                return state

            class TestState(TypedDict):
                messages: list

            workflow = StateGraph(TestState)
            workflow.add_node("my-agent", generate_message)
            workflow.set_entry_point("my-agent")
            workflow.add_edge("my-agent", END)

            app = workflow.compile()
            app.invoke(TestState(messages=[]))  # type: ignore[arg-type]

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        _, llm_call, request = finished_spans

        assert llm_call.attributes is not None
        llm_call_metadata = dict(json.loads(str(llm_call.attributes.get("metadata"))))
        assert llm_call_metadata.get("langgraph_node") == "my-agent"

        assert request.attributes is not None
        request_metadata = dict(json.loads(str(request.attributes.get("metadata"))))
        assert request_metadata.get("langgraph_node") == "my-agent"
