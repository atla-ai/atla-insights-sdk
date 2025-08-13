"""Basic instrumentation example."""

import os

from atla_insights import configure, instrument


@instrument("My instrumented function")
def my_instrumented_function() -> str:
    """My instrumented function."""
    return "Hello, world!"


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Calling the instrumented function will create a span behind the scenes
    my_instrumented_function()


if __name__ == "__main__":
    main()
