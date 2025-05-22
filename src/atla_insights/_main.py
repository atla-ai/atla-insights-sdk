"""Core functionality for the atla_package."""

import logging
import os
from typing import TYPE_CHECKING, ContextManager, Optional, Sequence, Union

import logfire
from opentelemetry.sdk.trace import SpanProcessor

from ._span_processors import (
    AtlaRootSpanProcessor,
    get_atla_root_span_processor,
    get_atla_span_processor,
)

if TYPE_CHECKING:
    from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger("atla_insights")


class AtlaInsights:
    """Atla insights."""

    def __init__(self) -> None:
        """Initialize Atla insights."""
        self._root_span_processor: Optional[AtlaRootSpanProcessor] = None
        self.configured = False

    def configure(
        self,
        token: str,
        metadata: Optional[dict[str, str]] = None,
        additional_span_processors: Optional[Sequence[SpanProcessor]] = None,
        verbose: bool = True,
    ) -> None:
        """Configure Atla insights.

        :param token (str): The write access token.
        :param metadata (Optional[dict[str, str]]): A dictionary of metadata to be added
            to the trace.
        :param additional_span_processors (Optional[Sequence[SpanProcessor]]): Additional
            span processors. Defaults to `None`.
        :param verbose (bool): Whether to print verbose output to console.
            Defaults to `True`.
        """
        if metadata and not all(
            isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()
        ):
            raise ValueError("The metadata field must be a mapping of string to string.")

        self.configured = True
        additional_span_processors = additional_span_processors or []

        self._root_span_processor = get_atla_root_span_processor(metadata)

        span_processors = [
            get_atla_span_processor(token),
            self._root_span_processor,
            *additional_span_processors,
        ]

        logfire.configure(
            additional_span_processors=span_processors,
            console=None if verbose else False,
            environment=os.getenv("_ATLA_ENV", "prod"),
            send_to_logfire=False,
            scrubbing=False,
        )

        logger.info("Atla insights configured correctly ✅")

    def mark_success(self) -> None:
        """Mark the root span in the current trace as successful."""
        if not self.configured or self._root_span_processor is None:
            raise ValueError(
                "Cannot mark trace before running the atla `configure` method."
            )
        self._root_span_processor.mark_root(value=1)
        logger.info("Marked trace as success ✅")

    def mark_failure(self) -> None:
        """Mark the root span in the current trace as failed."""
        if not self.configured or self._root_span_processor is None:
            raise ValueError(
                "Cannot mark trace before running the atla `configure` method."
            )
        self._root_span_processor.mark_root(value=0)
        logger.info("Marked trace as failure ❌")

    def instrument_openai(
        self,
        openai_client: Union[
            "OpenAI",
            "AsyncOpenAI",
            type["OpenAI"],
            type["AsyncOpenAI"],
            None,
        ] = None,
        openai_client_id: Optional[str] = None,
    ) -> ContextManager[None]:
        """Instrument OpenAI so that spans are automatically created for each request.

        :param openai_client: The OpenAI client to instrument. Defaults to `None`.
        :param openai_client_id (Optional[str]): The ID of the OpenAI client.
            Defaults to `None`.
        :return (ContextManager[None]): A context manager that instruments the OpenAI
            client.
        """
        if openai_client_id is None:
            return logfire.instrument_openai(openai_client)
        return logfire.with_settings(tags=[openai_client_id]).instrument_openai(
            openai_client
        )

    def instrument_litellm(self) -> None:
        """Instrument litellm."""
        try:
            import litellm
        except ImportError as e:
            raise ImportError(
                "Litellm needs to be installed in order to use the litellm integration. "
                "Please install it via `pip install litellm`."
            ) from e

        from ._litellm import AtlaLiteLLMOpenTelemetry

        atla_otel_logger = AtlaLiteLLMOpenTelemetry()
        if atla_otel_logger not in litellm.callbacks:
            litellm.callbacks.append(atla_otel_logger)


_ATLA = AtlaInsights()

configure = _ATLA.configure
mark_success = _ATLA.mark_success
mark_failure = _ATLA.mark_failure
instrument_litellm = _ATLA.instrument_litellm
instrument_openai = _ATLA.instrument_openai
