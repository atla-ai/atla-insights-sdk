"""LangGraph example."""

import os

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from atla_insights import configure, instrument, instrument_langchain


@instrument("My GenAI application")
def my_app(client: ChatOpenAI) -> None:
    """My LangGraph application."""

    def generate_message(state):
        messages = [HumanMessage(content="Hello, world!")]
        response = client.invoke(messages)
        state["messages"] = [*messages, response]
        return state

    class TestState(TypedDict):
        messages: list

    workflow = StateGraph(TestState)
    workflow.add_node("generate", generate_message)
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", END)

    app = workflow.compile()
    app.invoke({"messages": []})


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Create an async Anthropic client
    client = ChatOpenAI(model="gpt-4o-mini")

    # Instrument Anthropic
    instrument_langchain()

    # Calling the instrumented async Anthropic client will create spans behind the scenes
    my_app(client)


if __name__ == "__main__":
    main()
