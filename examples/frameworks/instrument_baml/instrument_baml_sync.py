"""BAML example.

See https://docs.boundaryml.com/guide/installation-language/python for details on
BAML setup for this example.
"""

import os

from baml_client.sync_client import b

from atla_insights import configure, instrument, instrument_baml


@instrument("My BAML application")
def my_app() -> None:
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

    response = b.ExtractResume(raw_resume)
    print(response)


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Instrument BAML with OpenAI
    instrument_baml("openai")

    # Calling the instrumented function will create spans behind the scenes
    my_app()


if __name__ == "__main__":
    main()
