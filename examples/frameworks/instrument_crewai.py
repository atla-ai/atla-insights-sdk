"""CrewAI example."""

from crewai import Agent, Crew, Process, Task

from atla_insights import configure, instrument_crewai

configure(token="")

instrument_crewai()

# Agent who comes up with ideas
idea_generator = Agent(
    role="Creative Idea Generator",
    goal="Brainstorm unique blog post ideas in the tech industry",
    backstory="You're a creative thinker who can spot trends and brainstorm exciting topics.",  # noqa: E501
    verbose=True,
)

# Agent who writes the blog post
writer = Agent(
    role="Tech Blogger",
    goal="Write engaging blog posts based on given ideas",
    backstory="You're a skilled writer who crafts informative and entertaining blog articles.",  # noqa: E501
    verbose=True,
    allow_delegation=False,
)

# Task 1: Brainstorm blog post ideas
idea_task = Task(
    description="Come up with 5 unique and interesting blog post ideas related to emerging technology.",  # noqa: E501
    expected_output="A numbered list of 5 blog post title ideas.",
    agent=idea_generator,
)

# Task 2: Write the blog post
write_task = Task(
    description="Choose the most interesting blog idea from the list and write a 3-paragraph blog post on it in markdown format.",  # noqa: E501
    expected_output="A markdown-formatted blog post with a title and three paragraphs.",
    agent=writer,
)

# Set up and run the crew
crew = Crew(
    agents=[idea_generator, writer],
    tasks=[idea_task, write_task],
    process=Process.sequential,
)

result = crew.kickoff()

print("\n\n📝 Final Blog Post:\n")
print(result)
