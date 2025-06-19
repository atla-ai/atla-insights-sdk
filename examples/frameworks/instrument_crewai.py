"""CrewAI example."""

import os

from crewai import Agent, Crew, Process, Task

from atla_insights import configure, instrument, instrument_crewai


@instrument("My GenAI application")
def my_app() -> None:
    """My CrewAI application."""
    idea_generator = Agent(
        role="Creative Idea Generator",
        goal="Brainstorm unique blog post ideas in the tech industry",
        backstory="You're a creative thinker who can brainstorm exciting topics.",
        verbose=True,
    )
    writer = Agent(
        role="Tech Blogger",
        goal="Write engaging blog posts based on given ideas",
        backstory="You're a skilled writer who crafts informative blog articles.",
        verbose=True,
        allow_delegation=False,
    )

    idea_task = Task(
        description="Come up with 5 interesting blog post ideas related to technology.",
        expected_output="A numbered list of 5 blog post title ideas.",
        agent=idea_generator,
    )
    write_task = Task(
        description="Choose the most interesting blog idea from the list and write a "
        "3-paragraph blog post on it in markdown format.",
        expected_output="A markdown-formatted blog post with a title and 3 paragraphs.",
        agent=writer,
    )

    crew = Crew(
        agents=[idea_generator, writer],
        tasks=[idea_task, write_task],
        process=Process.sequential,
    )

    result = crew.kickoff()

    print(result)


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument CrewAI
    instrument_crewai()

    # Invoking the instrumented CrewAI application will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
