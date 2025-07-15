"""BAML example.

See https://docs.boundaryml.com/guide/installation-language/python for details on
BAML setup for this example.
"""

import asyncio
import os

from baml_client.async_client import b

from atla_insights import configure, instrument, instrument_baml


@instrument("My BAML application")
async def my_app() -> None:
    """My application."""
    raw_resume = """
      Vaibhav Gupta
      vbv@boundaryml.com

      Experience:
      - Founder at BoundaryML
      - CV Engineer at Google
      - CV Engineer at Microsoft

      Skills:
      - Rust
      - C++
    """

    response = await b.ExtractResume(raw_resume)
    print(response)


async def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument BAML with OpenAI
    instrument_baml("openai")

    # Calling the instrumented function will create spans behind the scenes
    await my_app()


if __name__ == "__main__":
    asyncio.run(main())
