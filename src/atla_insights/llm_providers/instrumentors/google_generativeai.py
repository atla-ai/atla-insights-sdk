"""Google Generative AI instrumentation."""

import json
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Collection,
    Iterable,
    Iterator,
    Mapping,
    Tuple,
)

import opentelemetry.trace as trace_api
from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params.function_definition import FunctionDefinition
from openinference.instrumentation import OITracer, TraceConfig
from openinference.semconv.trace import (
    SpanAttributes,
    ToolAttributes,
)
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor  # type: ignore
from opentelemetry.trace import get_tracer, get_tracer_provider
from opentelemetry.util.types import AttributeValue
from wrapt import wrap_function_wrapper

try:
    from openinference.instrumentation.google_genai._stream import _Stream
    from openinference.instrumentation.google_genai._wrappers import (
        _AsyncGenerateContentStream,
        _AsyncGenerateContentWrapper,
        _SyncGenerateContent,
        _SyncGenerateContentStream,
    )

    from atla_insights.llm_providers.instrumentors.google_genai import (
        _get_tool_calls_from_content_parts,
    )
except ImportError as e:
    raise ImportError(
        "Google Generative AI instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[google-generativeai]"`.'
    ) from e


def iter_stream(stream: _Stream) -> Iterator[Any]:
    """Iterate over a stream and finish the tracing."""
    try:
        for item in stream.__wrapped__:
            stream._response_accumulator._is_null = False
            stream._response_accumulator._values += item.to_dict()
            yield item
    except Exception as exception:
        status = trace_api.Status(
            status_code=trace_api.StatusCode.ERROR,
            description=f"{type(exception).__name__}: {exception}",
        )
        stream._with_span.record_exception(exception)
        stream._finish_tracing(status=status)
        raise

    status = trace_api.Status(
        status_code=trace_api.StatusCode.OK,
    )
    stream._finish_tracing(status=status)


async def aiter_stream(stream: _Stream) -> AsyncIterator[Any]:
    """Iterate over a stream and finish the tracing."""
    try:
        async for item in stream.__wrapped__:
            stream._response_accumulator._is_null = False
            stream._response_accumulator._values += item.to_dict()
            yield item
    except Exception as exception:
        status = trace_api.Status(
            status_code=trace_api.StatusCode.ERROR,
            description=f"{type(exception).__name__}: {exception}",
        )
        stream._with_span.record_exception(exception)
        stream._finish_tracing(status=status)
        raise

    status = trace_api.Status(
        status_code=trace_api.StatusCode.OK,
    )
    stream._finish_tracing(status=status)


def _parse_function_declaration(function_declaration: object) -> str:
    """Parse a function declaration and return the attribute JSON schema value."""
    name = getattr(function_declaration, "name", "")
    description = getattr(function_declaration, "description", "")

    parameters = {}
    if function_parameters := getattr(function_declaration, "parameters", None):
        if json_schema := getattr(function_parameters, "json_schema", None):
            parameters = json_schema.model_dump(mode="json", exclude_none=True)

    tool_schema = ChatCompletionToolParam(
        type="function",
        function=FunctionDefinition(
            name=name,
            description=description,
            parameters=parameters,
            strict=None,
        ),
    )
    tool_schema_json = json.dumps(tool_schema)
    return tool_schema_json


def _get_tools_from_request(
    request_parameters: Mapping[str, Any],
) -> Iterator[Tuple[str, AttributeValue]]:
    """Get the tools from the request parameters."""
    tools = request_parameters.get("tools", None)
    if not tools:
        return

    tool_idx = 0
    for tool in tools:
        if not getattr(tool, "function_declarations", None):
            continue

        function_declarations = tool.function_declarations

        if not isinstance(function_declarations, Iterable):
            continue

        for function_declaration in function_declarations:
            tool_attr_name = ".".join(
                [
                    SpanAttributes.LLM_TOOLS,
                    str(tool_idx),
                    ToolAttributes.TOOL_JSON_SCHEMA,
                ]
            )
            yield (
                tool_attr_name,
                _parse_function_declaration(
                    function_declaration=function_declaration,
                ),
            )

            # Each function declaration is seen as a separate tool.
            tool_idx += 1


def _get_extra_attributes_from_request(
    wrapped: Callable[..., Any],
    instance: Any,
    args: Tuple[Any, ...],
    kwargs: Mapping[str, Any],
) -> Iterator[Tuple[str, AttributeValue]]:
    yield from wrapped(*args, **kwargs)
    yield from _get_tools_from_request(*args)


def _get_attributes_from_content_parts(
    wrapped: Callable[..., Any],
    instance: Any,
    args: Tuple[Any, ...],
    kwargs: Mapping[str, Any],
) -> Iterator[Tuple[str, AttributeValue]]:
    yield from wrapped(*args, **kwargs)
    yield from _get_tool_calls_from_content_parts(*args)


class _GenerateContent:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        wrap_function_wrapper(
            module="openinference.instrumentation.google_genai._request_attributes_extractor",
            name="_RequestAttributesExtractor.get_extra_attributes_from_request",
            wrapper=_get_extra_attributes_from_request,
        )
        self.generate_content = _SyncGenerateContent(*args, **kwargs)

        wrap_function_wrapper(
            module="openinference.instrumentation.google_genai._response_attributes_extractor",
            name="_ResponseAttributesExtractor._get_attributes_from_content_parts",
            wrapper=_get_attributes_from_content_parts,
        )
        self.generate_content_stream = _SyncGenerateContentStream(*args, **kwargs)

    def __call__(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: Tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        if kwargs.get("stream"):
            stream = self.generate_content_stream(wrapped, instance, args, kwargs)
            if isinstance(stream, _Stream):
                return iter_stream(stream)
            else:
                return stream
        else:
            return self.generate_content(wrapped, instance, args, kwargs)


class _AsyncGenerateContent:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.generate_content = _AsyncGenerateContentWrapper(*args, **kwargs)
        self.generate_content_stream = _AsyncGenerateContentStream(*args, **kwargs)

    async def __call__(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: Tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> AsyncIterator[Any]:
        if kwargs.get("stream"):
            stream = await self.generate_content_stream(wrapped, instance, args, kwargs)
            if isinstance(stream, _Stream):
                return aiter_stream(stream)
            else:
                return stream
        else:
            return await self.generate_content(wrapped, instance, args, kwargs)


class GoogleGenerativeAIInstrumentor(BaseInstrumentor):
    """An instrumentor for `google-generativeai`."""

    name = "google-generativeai"

    def instrumentation_dependencies(self) -> Collection[str]:
        """The instrumentation dependencies for `google-generativeai`."""
        return ("google-generativeai",)

    def _instrument(self, **kwargs: Any) -> None:
        if not (tracer_provider := kwargs.get("tracer_provider")):
            tracer_provider = get_tracer_provider()
        if not (config := kwargs.get("config")):
            config = TraceConfig()
        else:
            assert isinstance(config, TraceConfig)
        self._tracer = OITracer(
            get_tracer(
                instrumenting_module_name="openinference.instrumentation.google_genai",
                instrumenting_library_version="0.8.5",
                tracer_provider=tracer_provider,
            ),
            config=config,
        )

        try:
            from google.generativeai.generative_models import GenerativeModel
        except ImportError as err:
            raise Exception(
                "Could not import google-generativeai. "
                "Please install with `pip install google-generativeai`."
            ) from err

        self._original_generate_content = GenerativeModel.generate_content
        wrap_function_wrapper(
            module="google.generativeai.generative_models",
            name="GenerativeModel.generate_content",
            wrapper=_GenerateContent(tracer=self._tracer),
        )

        self._original_async_generate_content = GenerativeModel.generate_content_async
        wrap_function_wrapper(
            module="google.generativeai.generative_models",
            name="GenerativeModel.generate_content_async",
            wrapper=_AsyncGenerateContent(tracer=self._tracer),
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        from google.generativeai.generative_models import GenerativeModel

        if self._original_generate_content is not None:
            GenerativeModel.generate_content = (  # type: ignore[method-assign]
                self._original_generate_content
            )

        if self._original_async_generate_content is not None:
            GenerativeModel.generate_content_async = (  # type: ignore[method-assign]
                self._original_async_generate_content
            )
