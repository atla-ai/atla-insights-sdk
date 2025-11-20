"""ElevenLabs LLM provider instrumentation."""

import warnings
from typing import ContextManager, cast

import httpx
from opentelemetry.sdk.trace import TracerProvider

from atla_insights.constants import ELEVENLABS_API_KEY_VERIFY_ENDPOINT
from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import (
    NoOpContextManager,
    is_instrumentation_suppressed,
)


def _has_elevenlabs_api_key(url: str = ELEVENLABS_API_KEY_VERIFY_ENDPOINT) -> bool:
    """Verifies whether the authenticated user has uploaded a valid API key.

    :param url (str): ElevenLabs API key verification URL.
    :return (bool): Whether or not the user has a valid ElevenLabs API key.
    """
    with httpx.Client() as client:
        response = client.get(
            url,
            headers={
                "Authorization": f"Bearer {ATLA_INSTANCE.token}",
                "Content-Type": "application/json",
            },
        )

    if response.status_code != 200:
        warnings.warn(
            "Could not instrument ElevenLabs because we were unable to verify whether "
            "you have uploaded a valid ElevenLabs API key to the Atla platform. "
            "This should not happen. Please reach out to the Atla team for support.",
            stacklevel=1,
        )
        return False

    try:
        response_body = dict(response.json())
    except Exception:
        warnings.warn(
            "Could not instrument ElevenLabs because we were unable to verify whether "
            "you have uploaded a valid ElevenLabs API key to the Atla platform. "
            "This should not happen. Please reach out to the Atla team for support.",
            stacklevel=1,
        )
        return False

    has_api_key = bool(response_body.get("hasApiKey"))

    if has_api_key is False:
        warnings.warn(
            "Could not instrument ElevenLabs because you have not yet uploaded a valid "
            "ElevenLabs API key to the Atla platform. "
            "Please visit https://app.atla-ai.com and head to Organization > API key.",
            stacklevel=1,
        )

    return has_api_key


def instrument_elevenlabs() -> ContextManager[None]:
    """Instrument the ElevenLabs Python SDK.

    This function creates a context manager that instruments the ElevenLabs LLM
    provider, within its context.

    ```py
    from atla_insights import instrument_elevenlabs

    with instrument_elevenlabs():
        # My ElevenLabs code here
    ```

    :return (ContextManager[None]): A context manager that instruments ElevenLabs.
    """
    if is_instrumentation_suppressed() or not _has_elevenlabs_api_key():
        return NoOpContextManager()

    from atla_insights.llm_providers.instrumentors.elevenlabs import (
        AtlaElevenLabsInstrumentor,
    )

    tracer = cast(TracerProvider, ATLA_INSTANCE.tracer_provider).get_tracer(
        "openinference.instrumentation.elevenlabs"
    )
    instrumentor = AtlaElevenLabsInstrumentor(tracer=tracer)

    return ATLA_INSTANCE.instrument_service(
        service=AtlaElevenLabsInstrumentor.name,
        instrumentors=[instrumentor],
    )


def uninstrument_elevenlabs() -> None:
    """Uninstrument the ElevenLabs Python SDK."""
    if is_instrumentation_suppressed():
        return

    from atla_insights.llm_providers.instrumentors.elevenlabs import (
        AtlaElevenLabsInstrumentor,
    )

    ATLA_INSTANCE.uninstrument_service(AtlaElevenLabsInstrumentor.name)
