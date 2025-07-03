"""Instrument functions."""

import functools
import inspect
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Any, AsyncGenerator, Callable, Generator, Optional, overload

from opentelemetry.trace import Link, Tracer

from atla_insights.causal import get_current_links
from atla_insights.main import ATLA_INSTANCE, AtlaInsights, logger

executor: Optional[ThreadPoolExecutor]
try:
    from litellm.litellm_core_utils.thread_pool_executor import executor
except ImportError:
    executor = None


@overload
def instrument(func_or_message: Callable, *, capture_span: bool = False) -> Callable: ...


@overload
def instrument(
    func_or_message: Optional[str] = None, *, capture_span: bool = False
) -> Callable: ...


def instrument(
    func_or_message: Callable | Optional[str] = None,
    *,
    capture_span: bool = False,
) -> Callable:
    """Instruments a regular Python function.

    Can be used as either:
    ```py
    from atla_insights import instrument

    @instrument
    def my_function(a: int):
        ...
    ```

    or

    ```py
    from atla_insights import instrument

    @instrument("My function")
    def my_function(a: int):
        ...
    ```
    """
    # Case 1: used as bare decorator -> @instrument
    if callable(func_or_message) and not isinstance(func_or_message, str):
        func = func_or_message
        return _instrument(
            atla_instance=ATLA_INSTANCE, message=None, capture_span=capture_span
        )(func)

    # Case 2: called with message or parameters -> @instrument("msg", capture_span=True)
    return _instrument(
        atla_instance=ATLA_INSTANCE, message=func_or_message, capture_span=capture_span
    )


def _instrument(
    atla_instance: AtlaInsights,
    message: Optional[str],
    *,
    capture_span: bool = False,
) -> Callable:
    """Instrument a function.

    :param tracer (Optional[Tracer]): The tracer to use for instrumentation.
    :param message (Optional[str]): The message to use for the span.
    :return (Callable): A decorator that instruments the function.
    """

    def decorator(func: Callable) -> Callable:
        if inspect.isgeneratorfunction(func):

            @functools.wraps(func)
            def gen_wrapper(*args, **kwargs) -> Generator[Any, Any, Any]:
                if atla_instance.tracer is None:
                    logger.error("Atla Insights not configured, skipping instrumentation")
                    yield from func(*args, **kwargs)
                else:
                    with _start_span(atla_instance.tracer, message or func.__qualname__):
                        yield from func(*args, **kwargs)

            return gen_wrapper

        elif inspect.isasyncgenfunction(func):

            @functools.wraps(func)
            async def async_gen_wrapper(*args, **kwargs) -> AsyncGenerator[Any, Any]:
                if atla_instance.tracer is None:
                    logger.error("Atla Insights not configured, skipping instrumentation")
                    async for x in func(*args, **kwargs):
                        yield x
                else:
                    with _start_span(atla_instance.tracer, message or func.__qualname__):
                        async for x in func(*args, **kwargs):
                            yield x

            return async_gen_wrapper

        elif inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                if atla_instance.tracer is None:
                    logger.error("Atla Insights not configured, skipping instrumentation")
                    return await func(*args, **kwargs)

                with _start_span(
                    atla_instance.tracer, message or func.__qualname__
                ) as span:
                    result = await func(*args, **kwargs)
                    if capture_span:
                        return result, span
                    return result

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if atla_instance.tracer is None:
                logger.error("Atla Insights not configured, skipping instrumentation")
                return func(*args, **kwargs)

            with _start_span(atla_instance.tracer, message or func.__qualname__) as span:
                result = func(*args, **kwargs)
                if capture_span:
                    return result, span
                return result

        return sync_wrapper

    return decorator


@contextmanager
def _start_span(tracer: Tracer, span_name: str):
    """Start a new span in the tracer's current context.

    This context manager will also disable multithreaded litellm callbacks for the
    duration of the context.

    This is used to prevent a litellm ThreadPoolExecutor from scheduling callbacks in
    different threads, as these will only get executed after a thread lock is released,
    at which point the OTEL context is already lost.

    :param tracer (Tracer): The tracer to use for instrumentation.
    :param span_name (str): The name of the span.
    """
    # Build Link objects for any spans captured via ``link_from``
    source_spans = get_current_links()
    links = [Link(span.get_span_context()) for span in source_spans]

    with tracer.start_as_current_span(span_name, links=links if links else None) as span:
        if executor is not None:
            original_submit = executor.submit
            executor.submit = _execute_in_single_thread  # type: ignore[method-assign]

        yield span

        if executor is not None:
            executor.submit = original_submit  # type: ignore[method-assign]


def _execute_in_single_thread(fn: Callable, /, *args, **kwargs) -> Any:
    """Execute a function in a single thread."""
    return fn(*args, **kwargs)
