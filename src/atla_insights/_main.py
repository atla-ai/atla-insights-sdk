"""Core functionality for the atla_package."""

import logging
import os
from typing import (
    TYPE_CHECKING,
    ContextManager,
    Optional,
    Sequence,
    Union,
)

import logfire
from opentelemetry.sdk.trace import SpanProcessor

from ._constants import SUPPORTED_LLM_PROVIDER
from ._span_processors import (
    AtlaRootSpanProcessor,
    get_atla_root_span_processor,
    get_atla_span_processor,
)
from ._utils import validate_metadata

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
        validate_metadata(metadata)

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
        self.configured = True

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

    def instrument_anthropic(self) -> None:
        """Instrument Anthropic."""
        try:
            from openinference.instrumentation.anthropic import AnthropicInstrumentor
            from openinference.instrumentation.anthropic._wrappers import (
                _AsyncMessagesWrapper,
                _MessagesWrapper,
            )
            from wrapt import wrap_function_wrapper
        except ImportError as e:
            raise ImportError(
                "Anthropic instrumentation needs to be installed. "
                "Please install it via `pip install atla-insights[anthropic]`."
            ) from e

        instrumentor = AnthropicInstrumentor()
        instrumentor.instrument()

        wrap_function_wrapper(
            module="anthropic.resources.beta.messages",
            name="Messages.create",
            wrapper=_MessagesWrapper(tracer=instrumentor._tracer),
        )
        wrap_function_wrapper(
            module="anthropic.resources.beta.messages",
            name="AsyncMessages.create",
            wrapper=_AsyncMessagesWrapper(tracer=instrumentor._tracer),
        )

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

    def instrument_langchain(self) -> None:
        """Instrument the Langchain framework."""
        try:
            from openinference.instrumentation.langchain import LangChainInstrumentor
        except ImportError as e:
            raise ImportError(
                "Langchain instrumentation needs to be installed. "
                "Please install it via `pip install atla-insights[langchain]`."
            ) from e

        LangChainInstrumentor().instrument()

    def instrument_litellm(self) -> None:
        """Instrument litellm."""
        try:
            import litellm
        except ImportError as e:
            raise ImportError(
                "Litellm needs to be installed. "
                "Please install it via `pip install atla-insights[litellm]`."
            ) from e

        from ._litellm import AtlaLiteLLMOpenTelemetry

        atla_otel_logger = AtlaLiteLLMOpenTelemetry()
        if atla_otel_logger not in litellm.callbacks:
            litellm.callbacks.append(atla_otel_logger)

    def _instrument_llm_provider(
        self,
        llm_provider: Union[Sequence[SUPPORTED_LLM_PROVIDER], SUPPORTED_LLM_PROVIDER],
    ) -> None:
        """Instrument an LLM provider.

        :param llm_provider (Union[Sequence[SUPPORTED_LLM_PROVIDER],
            SUPPORTED_LLM_PROVIDER]): The LLM provider(s) to instrument.
        :raises (ValueError): If the LLM provider is invalid.
        """
        if isinstance(llm_provider, str):
            llm_provider = [llm_provider]

        for provider in set(llm_provider):
            match provider:
                case "anthropic":
                    self.instrument_anthropic()
                case "openai":
                    self.instrument_openai()
                case "litellm":
                    self.instrument_litellm()
                case _:
                    raise ValueError(f"Invalid LLM provider: {provider}")

    def instrument_agno(
        self,
        llm_provider: Union[Sequence[SUPPORTED_LLM_PROVIDER], SUPPORTED_LLM_PROVIDER],
    ) -> None:
        """Instrument the Agno framework.

        :param llm_provider (Union[Sequence[SUPPORTED_LLM_PROVIDER],
            SUPPORTED_LLM_PROVIDER]): The LLM provider(s) to instrument.
        """
        try:
            from openinference.instrumentation.agno import AgnoInstrumentor
        except ImportError as e:
            raise ImportError(
                "Agno instrumentation needs to be installed. "
                "Please install it via `pip install atla-insights[agno]`."
            ) from e

        AgnoInstrumentor().instrument()
        self._instrument_llm_provider(llm_provider)

    def instrument_mcp(self) -> None:
        """Instrument MCP."""
        try:
            from openinference.instrumentation.mcp import MCPInstrumentor
        except ImportError as e:
            raise ImportError(
                "MCP instrumentation needs to be installed. "
                "Please install it via `pip install atla-insights[mcp]`."
            ) from e

        MCPInstrumentor().instrument()

    def instrument_smolagents(
        self,
        llm_provider: Union[Sequence[SUPPORTED_LLM_PROVIDER], SUPPORTED_LLM_PROVIDER],
    ) -> None:
        """Instrument the HuggingFace Smolagents framework.

        :param llm_provider (Union[Sequence[SUPPORTED_LLM_PROVIDER],
            SUPPORTED_LLM_PROVIDER]): The LLM provider(s) to instrument.
        """
        try:
            from openinference.instrumentation.smolagents import SmolagentsInstrumentor
        except ImportError as e:
            raise ImportError(
                "Smolagents instrumentation needs to be installed. "
                "Please install it via `pip install atla-insights[smolagents]`."
            ) from e

        SmolagentsInstrumentor().instrument()
        self._instrument_llm_provider(llm_provider)


_ATLA = AtlaInsights()

configure = _ATLA.configure
mark_success = _ATLA.mark_success
mark_failure = _ATLA.mark_failure
instrument_agno = _ATLA.instrument_agno
instrument_anthropic = _ATLA.instrument_anthropic
instrument_langchain = _ATLA.instrument_langchain
instrument_litellm = _ATLA.instrument_litellm
instrument_mcp = _ATLA.instrument_mcp
instrument_openai = _ATLA.instrument_openai
instrument_smolagents = _ATLA.instrument_smolagents
