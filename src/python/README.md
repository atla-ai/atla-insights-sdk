# Atla Insights [Python]

<p align="center">
  <a href="https://badge.fury.io/py/atla-insights"><img src="https://badge.fury.io/py/atla-insights.svg" alt="PyPI version"></a>
</p>

## Getting started

To get started with Atla Insights, you can either follow the instructions below, or let an agent instrument your code for you.

-   **If you are using Claude Code**: copy the contents of `Claude.md`.
-   **If you are not using Claude Code**: copy the contents of `onboarding.txt` and paste them into your AI agent of choice.

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

# Run this command at the start of your application.
configure(token="<MY_ATLA_INSIGHTS_TOKEN>")
```

You can retrieve your authentication token from the [Atla Insights platform](https://app.atla-ai.com).

### Instrumentation

In order for spans/traces to become available in your Atla Insights dashboard, you will
need to add some form of instrumentation.

As a starting point, you will want to instrument your GenAI library of choice.

See the section below to find out which frameworks & providers we currently support.

All instrumentation methods share a common interface, which allows you to do the following:

-   **Session-wide (un)instrumentation**:
    You can manually enable/disable instrumentation throughout your application.

```python
from atla_insights import configure, instrument_my_framework, uninstrument_my_framework

configure(...)
instrument_my_framework()

# All framework code from this point onwards will be instrumented

uninstrument_my_framework()

# All framework code from this point onwards will **no longer** be instrumented
```

-   **Instrumented contexts**:
    All instrumentation methods also behave as context managers that automatically handle (un)instrumentation.

```python
from atla_insights import configure, instrument_my_framework

configure()

with instrument_my_framework():
    # All framework code inside the context will be instrumented

# All framework code outside the context **not** be instrumented
```

### Instrumentation Support

#### Providers

We currently support the following LLM providers:

| Provider         | Instrumentation Function  | Notes                                                  |
| ---------------- | ------------------------- | ------------------------------------------------------ |
| **Anthropic**    | `instrument_anthropic`    | Also supports `AnthropicBedrock` client from Anthropic |
| **Google GenAI** | `instrument_google_genai` | E.g., Gemini                                           |
| **LiteLLM**      | `instrument_litellm`      | Supports all available models in the LiteLLM framework |
| **OpenAI**       | `instrument_openai`       | Includes Azure OpenAI                                  |
| **Bedrock**      | `instrument_bedrock`      |                                                        |

⚠️ Note that, by default, instrumented LLM calls will be treated independently from one
another. In order to logically group LLM calls into a trace, you will need to group them
as follows:

```python
from atla_insights import configure, instrument, instrument_litellm
from litellm import completion

configure(...)
instrument_litellm()

# The LiteLLM calls below will belong to **separate traces**
result_1 = completion(...)
result_2 = completion(...)

@instrument("My agent doing its thing")
def run_my_agent() -> None:
    # The LiteLLM calls within this function will belong to the **same trace**
    result_1 = completion(...)
    result_2 = completion(...)
    ...
```

#### Frameworks

We currently support the following frameworks:

| Framework         | Instrumentation Function   | Notes                                                                                                       |
| ----------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Agno**          | `instrument_agno`          | Supported with `openai`, `google-genai`, `litellm` and/or `anthropic` models\*                              |
| **BAML**          | `instrument_baml`          | Supported with `openai`, `anthropic` or `bedrock` models\*                                                  |
| **CrewAI**        | `instrument_crewai`        |                                                                                                             |
| **LangChain**     | `instrument_langchain`     | This includes e.g., LangGraph as well                                                                       |
| **MCP**           | `instrument_mcp`           | Only includes context propagation. You will need to instrument the model calling the MCP server separately. |
| **OpenAI Agents** | `instrument_openai_agents` | Supported with `openai`, `google-genai`, `litellm` and/or `anthropic` models\*                              |
| **Smolagents**    | `instrument_smolagents`    | Supported with `openai`, `google-genai`, `litellm` and/or `anthropic` models\*                              |

⚠️ \*Note that some frameworks do not provide their own LLM interface. In these cases, you will
need to instrument both the framework _and_ the underlying LLM provider(s) as follows:

```python
from atla_insights import configure, instrument, instrument_agno

configure(...)

# If you are using a single LLM provider (e.g., via `OpenAIChat`).
instrument_agno("openai")

# If you are using multiple LLM providers (e.g., `OpenAIChat` and `Claude`).
instrument_agno(["anthropic", "openai"])
```

#### Manual instrumentation

It is also possible to manually record LLM generations using the lower-level span SDK.

```python
from atla_insights.span import start_as_current_span

with start_as_current_span("my-llm-generation") as span:
    # Run my LLM generation via an unsupported framework.
    input_messages = [{"role": "user", "content": "What is the capital of France?"}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_capital",
                "parameters": {"type": "object", "properties": {"country": {"type": "string"}}},
            },
        }
    ]
    result = my_client.chat.completions.create(messages=input_messages, tools=tools)

    # Manually record LLM generation.
    span.record_generation(
        input_messages=input_messages,
        output_messages=[choice.message for choice in result.choices],
        tools=tools,
    )

```

Note that the expected data format are OpenAI Chat Completions compatible messages / tools.

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

### Tool invocations

If you want to ensure your function-based tool calls are logged correctly, you can wrap
them using the `@tool` decorator as follows:

```python
from atla_insights import tool

@tool
def my_tool(my_arg: str) -> str:
    return "some-output"
```

⚠️ Note that if you are using an instrumented framework, you do **not** need to manually
decorate your tools in this way.

### Sampling

By default, Atla Insights will instrument & log all traces. In high-throughput scenarios,
you may not want to log every trace you produce. In these cases, you can specify a
sampler at configuration time.

-   **Using a built-in sampling method**:

If you want a basic, reliable sampler, you can use one of our pre-built sampling methods.

```python
from atla_insights import configure
from atla_insights.sampling import TraceRatioSamplingOptions

# We want to log 10% of traces
sampling_options = TraceRatioSamplingOptions(rate=0.10)

configure(
    token="<MY_ATLA_INSIGHTS_TOKEN>",
    sampling=sampling_options,
)
```

-   **Using a custom sampling method**:

If you want to implement your own custom sampling method, you can pass in your own
[OpenTelemery Sampler](https://opentelemetry-python.readthedocs.io/en/latest/sdk/trace.sampling.html).

```python
from atla_insights import configure
from opentelemetry.sdk.trace.sampling import Sampler

class MySampler(Sampler):
    ...

my_sampler = MySampler()

configure(
    token="<MY_ATLA_INSIGHTS_TOKEN>",
    sampling=my_sampler,
)
```

⚠️ Note that the Atla Insights platform is **not** intended to work well with partial
traces. Therefore, we highly recommend using either `ParentBased` or `StaticSampler`
samplers. This ensures either all traces are treated the same way or all spans in the
same trace are treated the same way.

```python
from atla_insights import configure
from opentelemetry.sdk.trace.sampling import ParentBased, Sampler

class MySampler(Sampler):
    ...

my_sampler = ParentBased(root=MySampler())

configure(
    token="<MY_ATLA_INSIGHTS_TOKEN>",
    sampling=my_sampler,
)
```

### Adding custom metrics

You can add custom evaluation metrics to your trace.

```python
from atla_insights import instrument, set_custom_metrics

@instrument()
def my_function():
    # Some GenAI logic here
    eval_result = False
    set_custom_metrics({"my_metric": {"data_type": "boolean", "value": eval_result}})
```

The permitted `data_type` fields are:

-   `likert_1_to_5`: a numeric 1-5 scale. In this case, `value` is expected to be an `int` between 1 and 5.
-   `boolean`: a boolean scale. In this case, `value` is expected to be a `bool`.

The primary intended use case is logging custom code evals that benefit from being in the
active runtime environment. You can, however, log any arbitrary metric - including custom
LLMJ eval results.

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

E.g., the following code snippet will make tracing available in both Atla and Langfuse.

```python
from atla_insights import configure, instrument_openai
from langfuse.openai import OpenAI

configure(...)

instrument_openai()

client = OpenAI()
client.chat.completions.create(...)
```

#### OpenTelemetry compatibility

The Atla Insights SDK is built on the OpenTelemetry standard and fully compatible with
other OpenTelemetry services.

If you have an existing OpenTelemetry setup (e.g., by setting the relevant otel
environment variables), Atla Insights will be _additive_ to this setup. I.e., it will add
additional logging on top of what is already getting logged.

If you do not have an existing OpenTelemetry setup, Atla Insights will initialize a new
(global) tracer provider.

Next to the above, you also have the ability to add any arbitrary additional span
processors by following the example below:

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
