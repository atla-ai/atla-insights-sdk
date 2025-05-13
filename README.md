# Atla Insights

Atla is a platform for monitoring and improving AI agents.

## Installation

```bash
pip install atla-insights
```

To install package-specific dependencies:

```bash
pip install "atla-insights[litellm]"
```

## Usage

### Configuration

Before using Atla Insights, you need to configure it with your authentication token:

```python
from atla_insights import configure

configure(token="<MY_ATLA_INSIGHTS_TOKEN>")
```

### Instrumentation

In order for spans/traces to become available in your Atla Insights dashboard, you will
need to add some form of instrumentation.

As a starting point, you will want to instrument your GenAI library of choice.

We currently support the following:

#### OpenAI chat completions
You can instrument the entire OpenAI library via

```python
from atla_insights import configure, instrument_openai
from openai import OpenAI

configure(...)

instrument_openai()

# Every subsequent OpenAI or AsyncOpenAI SDK chat completions call will be automatically instrumented.
client = OpenAI()
client.chat.completions.create(...)
```

Alternatively, you can also instrument an individual client.

```python
from atla_insights import configure, instrument_openai
from openai import OpenAI

configure(...)

client_1 = OpenAI()
client_2 = OpenAI()

instrument_openai(client_1)

client_1.chat.completions.create(...)  # this call will be instrumented
client_2.chat.completions.create(...)  # this call will not
```

#### LiteLLM
You can instrument litellm (sync and async) completions via:

```python
from atla_insights import configure, instrument_litellm
from litellm import completion

configure(...)

instrument_litellm()

# Every subsequent litellm completion or acompletion call will be automatically instrumented.
completion(...)
```

⚠️ Note that, by default, instrumented LLM calls will be treated independently from one
another. In order to logically group LLM calls into a trace, you will need to group them
as follows:

```python
from atla_insights import configure, instrument, instrument_litellm
from litellm import completion

configure(...)
instrument_litellm()

@instrument("My agent doing its thing")
def run_my_agent() -> None:
    """The LiteLLM calls within this function will belong to the same trace and treated
    as subsequent steps in a single logical flow."""
    result_1 = completion(...)
    result_2 = completion(...)
    ...
```

### Adding metadata

You can attach metadata to a run that provides additional information about the specs of
that specific workflow. This can include various system settings, prompt versions, etc.

```python
from atla_insights import configure

# We can define some system settings, prompt versions, etc. we'd like to keep track of.
metadata = {
    "environment": "dev",
    "prompt-version": "v1.4",
    "model": "gpt-4o-2024-08-06",
    "run-id": "my-test",
}

# Any subsequent generated traces will inherit the metadata specified here.
configure(
    token="<MY_ATLA_INSIGHTS_TOKEN>",
    metadata=metadata,
)
```


### Marking trace success / failure

The logical notion of _success_ or _failure_ plays a prominent role in the observability
of (agentic) GenAI applications.

Therefore, the `atla_insights` package offers the functionality to mark a trace as a
success or a failure like follows:

```python
from atla_insights import (
    configure,
    instrument,
    instrument_openai,
    mark_failure,
    mark_success,
)
from openai import OpenAI

configure(...)
instrument_openai()

client = OpenAI()

@instrument("My agent doing its thing")
def run_my_agent() -> None:
    result = client.chat.completions.create(
        model=...,
        messages=[
            {
                "role": "user",
                "content": "What is 1 + 2? Reply with only the answer, nothing else.",
            }
        ]
    )
    response = result.choices[0].message.content

    # Note that you could have any arbitrary success condition, including LLMJ-based evaluations
    if response == "3":
        mark_success()
    else:
        mark_failure()
```

⚠️ Note that you should use this marking functionality within an instrumented function.

### Compatibility with existing observability

As `atla_insights` provides its own instrumentation, we should note potential interactions
with our instrumentation / observability providers.

`atla_insights` instrumentation is generally compatible with most popular observability
platforms.

E.g. the following code snippet will make tracing available in both Atla and LangFuse.

```python
from atla_insights import configure, instrument_openai
from langfuse.openai import OpenAI

configure(...)

instrument_openai()

client = OpenAI()
client.chat.completions.create(...)
```

#### OpenTelemetry compatibility

Next to the above, you also have the ability to export traces to any arbitrary additional
opentelemetry provider by following this example:

```python
from atla_insights import configure
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

# This is the otel traces endpoint for my provider of choice.
my_otel_endpoint = "https://my-otel-provider/v1/traces"

my_span_exporter = OTLPSpanExporter(endpoint=my_otel_endpoint)
my_span_processor = SimpleSpanProcessor(my_span_exporter)

configure(
    token="<MY_ATLA_INSIGHTS_TOKEN>",
    # This will ensure traces get sent to my otel provider of choice
    additional_span_processors=[my_span_processor],
)
```

### More examples

More specific examples can be found in the `examples/` folder.
