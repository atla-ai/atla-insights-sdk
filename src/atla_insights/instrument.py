"""Instrument functions."""

import functools
import inspect
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Any, AsyncGenerator, Callable, Generator, Optional, overload

from opentelemetry.trace import Tracer

from atla_insights.main import ATLA_INSTANCE, AtlaInsights, logger

executor: Optional[ThreadPoolExecutor]
try:
    from litellm.litellm_core_utils.thread_pool_executor import executor
except ImportError:
    executor = None


@overload
def instrument(func_or_message: Callable) -> Callable: ...


@overload
def instrument(func_or_message: Optional[str] = None) -> Callable: ...


def instrument(func_or_message: Callable | Optional[str] = None) -> Callable:
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
    if callable(func_or_message):
        return instrument()(func=func_or_message)
    return _instrument(atla_instance=ATLA_INSTANCE, message=func_or_message)


def _instrument(atla_instance: AtlaInsights, message: Optional[str]) -> Callable:
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

                with _start_span(atla_instance.tracer, message or func.__qualname__):
                    return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if atla_instance.tracer is None:
                logger.error("Atla Insights not configured, skipping instrumentation")
                return func(*args, **kwargs)

            with _start_span(atla_instance.tracer, message or func.__qualname__):
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator


@contextmanager
def _start_span(tracer: Tracer, span_name: str) -> Generator:
    """Start a new span in the tracer's current context.

    This context manager will also disable multithreaded litellm callbacks for the
    duration of the context.

    This is used to prevent a litellm ThreadPoolExecutor from scheduling callbacks in
    different threads, as these will only get executed after a thread lock is released,
    at which point the OTEL context is already lost.

    :param tracer (Tracer): The tracer to use for instrumentation.
    :param span_name (str): The name of the span.
    """
    with tracer.start_as_current_span(span_name):
        if executor is not None:
            original_submit = executor.submit
            executor.submit = _execute_in_single_thread  # type: ignore[method-assign]

        yield

        if executor is not None:
            executor.submit = original_submit  # type: ignore[method-assign]


def _execute_in_single_thread(fn: Callable, /, *args, **kwargs) -> Any:
    """Execute a function in a single thread."""
    return fn(*args, **kwargs)
