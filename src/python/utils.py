"""Utility functions for Atla Insights."""

import importlib

import opentelemetry.trace
from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider
from opentelemetry.trace import ProxyTracerProvider, get_tracer_provider


def truncate_value(value: str, max_chars: int) -> str:
    """Truncate a value to a maximum number of characters.

    :param value (str): The value to truncate.
    :param max_chars (int): The maximum number of characters to allow.
    :return (str): The truncated value.
    """
    if len(value) > max_chars:
        return value[: (max_chars - 3)] + "..."
    return value


def maybe_get_existing_tracer_provider() -> SDKTracerProvider | None:
    """Get the existing tracer provider, if it exists."""
    existing_tracer_provider = get_tracer_provider()

    # If the existing tracer provider is a proxy, there is no existing OTEL setup.
    if isinstance(existing_tracer_provider, ProxyTracerProvider):
        return None

    # If there is an API tracer provider, but not an SDK tracer provider, it is a no-op
    # and we reload the module so we can reset the tracer provider safely.
    if not isinstance(existing_tracer_provider, SDKTracerProvider):
        importlib.reload(opentelemetry.trace)
        return None

    return existing_tracer_provider
