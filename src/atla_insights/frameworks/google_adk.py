"""Google Agent Development Kit (ADK) instrumentation logic."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import NoOpContextManager, is_instrumentation_suppressed


def instrument_google_adk() -> ContextManager[None]:
    """Instrument the Google Agent Development Kit (ADK) framework.

    This function creates a context manager that instruments the ADK framework, within
    its context, and for certain provided LLM provider(s).

    See [Google ADK docs](https://google.github.io/adk-docs/) for usage details on the
    framework itself.

    ```py
    from atla_insights import instrument_google_adk

    with instrument_google_adk():
        # My ADK code here
    ```

    :return (ContextManager[None]): A context manager that instruments ADK.
    """
    if is_instrumentation_suppressed():
        return NoOpContextManager()

    try:
        from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    except ImportError as e:
        raise ImportError(
            "Google ADK instrumentation needs to be installed. "
            'Please install it via `pip install "atla-insights[google-adk]"`.'
        ) from e

    # Create an instrumentor for the Google ADK framework.
    google_adk_instrumentor = GoogleADKInstrumentor()

    return ATLA_INSTANCE.instrument_service(
        service="google-adk",
        instrumentors=[google_adk_instrumentor],
    )


def uninstrument_google_adk() -> None:
    """Uninstrument the Google ADK framework."""
    if is_instrumentation_suppressed():
        return

    return ATLA_INSTANCE.uninstrument_service("google-adk")
