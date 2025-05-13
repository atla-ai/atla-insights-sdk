"""Nested instrumentation example."""

import os

from atla_insights import configure, instrument


@instrument("My nested function")
def my_nested_function() -> str:
    """My nested function."""
    return "Hello, world!"


@instrument("My instrumented function")
def my_instrumented_function() -> str:
    """My instrumented function."""
    result = my_nested_function()
    return result


def main() -> None:
    """Main function."""
    # Configure the client
    configure(token=os.environ["ATLA_INSIGHTS_TOKEN"])

    # Calling the instrumented function will create nested spans behind the scenes
    my_instrumented_function()


if __name__ == "__main__":
    main()
