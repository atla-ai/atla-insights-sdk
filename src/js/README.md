# Atla Insights TypeScript SDK

TypeScript/JavaScript SDK for monitoring and observability of AI agents using the Atla Insights platform.

<p align="center">
  <a href="https://www.npmjs.com/package/@atla/insights-sdk"><img src="https://img.shields.io/npm/v/@atla/insights-sdk.svg" alt="npm version"></a>
  <a href="https://github.com/atla-ai/atla-insights-sdk/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square" alt="license" /></a>
  <a href="https://app.atla-ai.com"><img src="https://img.shields.io/badge/Atla_Insights_platform-white?logo=data:image/svg%2bxml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBzdGFuZGFsb25lPSJubyI/Pgo8IURPQ1RZUEUgc3ZnIFBVQkxJQyAiLS8vVzNDLy9EVEQgU1ZHIDIwMDEwOTA0Ly9FTiIKICJodHRwOi8vd3d3LnczLm9yZy9UUi8yMDAxL1JFQy1TVkctMjAwMTA5MDQvRFREL3N2ZzEwLmR0ZCI+CjxzdmcgdmVyc2lvbj0iMS4wIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiB3aWR0aD0iMjAwLjAwMDAwMHB0IiBoZWlnaHQ9IjIwMC4wMDAwMDBwdCIgdmlld0JveD0iMCAwIDIwMC4wMDAwMDAgMjAwLjAwMDAwMCIKIHByZXNlcnZlQXNwZWN0UmF0aW89InhNaWRZTWlkIG1lZXQiPgoKPGcgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMC4wMDAwMDAsMjAwLjAwMDAwMCkgc2NhbGUoMC4xMDAwMDAsLTAuMTAwMDAwKSIKZmlsbD0iIzAwMDAwMCIgc3Ryb2tlPSJub25lIj4KPHBhdGggZD0iTTEyODUgMTQ1MCBjLTM2IC0zNyAtNDcgLTU0IC00MCAtNjMgNDAgLTU0IDc4IC0xMTkgOTYgLTE2NyAxNyAtNDYKMjAgLTcyIDE3IC0xNTUgLTMgLTg3IC04IC0xMDkgLTM1IC0xNjggLTQwIC04NCAtMTI1IC0xNzEgLTIwNSAtMjA5IC0xNTIgLTc0Ci0zMjcgLTU2IC00NjIgNDcgbC00OSAzNyAtNDggLTQ4IGMtMjcgLTI3IC00OSAtNTMgLTQ5IC01OSAwIC0xNyA5MCAtODIgMTYyCi0xMTUgMjM1IC0xMTAgNTA0IC01OSA2ODMgMTMxIDE1MCAxNjAgMjAyIDM4NyAxMzQgNTkzIC0yNCA3MyAtMTE1IDIxOSAtMTM5CjIyNCAtOSAxIC0zOCAtMjAgLTY1IC00OHoiLz4KPHBhdGggZD0iTTgxNSAxNDE5IGMtMjYwIC04NCAtMzMwIC00MTQgLTEyOCAtNTk5IDc2IC02OSAxNDQgLTkzIDI1MyAtODggMTQyCjcgMjQxIDcxIDMwMiAxOTYgMzAgNjEgMzMgNzUgMzMgMTU3IC0xIDc3IC01IDk4IC0yOCAxNDUgLTQ2IDk1IC0xMjEgMTYxCi0yMTggMTkxIC03NiAyNCAtMTM3IDIzIC0yMTQgLTJ6Ii8+CjwvZz4KPC9zdmc+Cg==" alt="Atla Insights platform"></a>
</p>

## Installation

```bash
npm install @atla/insights-sdk
```

Or with pnpm (recommended):

```bash
pnpm add @atla/insights-sdk
```

## Development Setup

This SDK uses:

-   **pnpm** as the package manager (`pnpm@10.14.0`)
-   **Biome** for TypeScript/JavaScript linting and formatting
-   **Prettier** for JSON/JSONC formatting

```bash
# Install dependencies
pnpm install

# Run Biome checks
pnpm exec biome check --write

# Run tests
pnpm test
```

## Usage

### Configuration

Configure the SDK with your authentication token at the start of your application:

```typescript
import { configure } from "@atla/insights-sdk";

// Basic configuration
configure({
    token: process.env.ATLA_INSIGHTS_TOKEN!,
    serviceName: "my-ai-app", // Optional, defaults to "atla-insights-js"
});

// With global metadata
configure({
    token: process.env.ATLA_INSIGHTS_TOKEN!,
    metadata: {
        environment: "production",
        version: "1.2.3",
        "model-version": "gpt-4-turbo",
    },
});
```

You can retrieve your authentication token from the [Atla Insights platform](https://app.atla-ai.com).

### Instrumentation

#### LLM Provider Instrumentation

We currently support the following LLM providers:

| Provider   | Instrumentation Function | Notes                         |
| ---------- | ------------------------ | ----------------------------- |
| **OpenAI** | `instrumentOpenAI`       | Includes Azure OpenAI support |

```typescript
import { configure, instrumentOpenAI } from "@atla/insights-sdk";
import OpenAI from "openai";

// Configure SDK
configure({ token: process.env.ATLA_INSIGHTS_TOKEN! });

// Enable OpenAI instrumentation globally
instrumentOpenAI();

// Use OpenAI normally - all calls will be automatically traced
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const completion = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [{ role: "user", content: "What is observability?" }],
});
```

#### Function Instrumentation

Group related operations into traces using the `@instrument` decorator:

```typescript
import { instrument, markSuccess, markFailure } from "@atla/insights-sdk";

class MyAgent {
    @instrument("processUserQuery")
    async processUserQuery(query: string) {
        try {
            // Multiple LLM calls will be grouped in the same trace
            const planning = await this.planResponse(query);
            const result = await this.executeResponse(planning);

            if (result.isValid) {
                markSuccess();
            } else {
                markFailure();
            }

            return result;
        } catch (error) {
            markFailure();
            throw error;
        }
    }
}

// Or use as a regular function wrapper
const processQuery = instrument("processQuery")(async (query: string) => {
    // Your logic here
});
```

#### Manual Instrumentation

For fine-grained control or unsupported providers:

```typescript
import { startAsCurrentSpan } from "@atla/insights-sdk";

await startAsCurrentSpan("custom-llm-operation", async (span) => {
    const inputMessages = [{ role: "user", content: "Explain quantum computing" }];

    // Call your LLM
    const response = await myCustomLLM.generate(inputMessages);

    // Record the generation with OpenAI-compatible format
    span.recordGeneration({
        inputMessages,
        outputMessages: [{ role: "assistant", content: response.text }],
        model: "custom-model-v1",
        modelParameters: {
            temperature: 0.7,
            max_tokens: 1000,
        },
    });
});
```

### Metadata Management

Add contextual information to your traces:

```typescript
import { setMetadata, withMetadata } from "@atla/insights-sdk";

// Set metadata for current trace
@instrument("myFunction")
async function myFunction() {
  setMetadata({
    userId: "user-123",
    requestId: "req-456",
    feature: "chat-assistant",
  });
  // Your code here
}

// Or use with context
await withMetadata({ experimentId: "exp-789" }, async () => {
  // All operations here will include this metadata
  await someOperation();
});
```

### Success/Failure Marking

Mark traces based on your business logic:

```typescript
import { instrument, markSuccess, markFailure } from "@atla/insights-sdk";

@instrument("validateResponse")
async function validateResponse(response: string) {
  // Custom validation logic
  if (response.includes("correct answer")) {
    markSuccess();
    return { valid: true };
  } else {
    markFailure();
    return { valid: false };
  }
}
```

### Nested Instrumentation

The SDK supports nested instrumentation for complex workflows:

```typescript
@instrument("parentOperation")
async function parentOperation() {
  const result1 = await childOperation1();
  const result2 = await childOperation2();
  return { result1, result2 };
}

@instrument("childOperation1")
async function childOperation1() {
  // This will be a child span of parentOperation
  return await someWork();
}
```

## Examples

Check out the `examples/` directory for complete working examples:

-   `examples/basic_instrumentation.ts` - Basic instrumentation example
-   `examples/instrument_openai.ts` - OpenAI integration with debug logging
-   `examples/nested_instrumentation.ts` - Nested instrumentation patterns

Run examples:

```bash
# Basic example
npx tsx examples/basic_instrumentation.ts

# OpenAI example (requires OPENAI_API_KEY)
npx tsx examples/instrument_openai.ts
```

## API Reference

### Core Functions

-   `configure(options: ConfigureOptions)` - Initialize the SDK
-   `instrument(name?: string)` - Decorator/wrapper for function instrumentation
-   `startAsCurrentSpan(name, fn)` - Manual span creation

### Metadata & Marking

-   `setMetadata(metadata)` - Set metadata for current trace
-   `getMetadata()` - Get current metadata
-   `withMetadata(metadata, fn)` - Run function with additional metadata
-   `clearMetadata()` - Clear runtime metadata
-   `markSuccess()` - Mark current trace as successful
-   `markFailure()` - Mark current trace as failed

### Provider Instrumentation

-   `instrumentOpenAI()` - Enable OpenAI instrumentation
-   `uninstrumentOpenAI()` - Disable OpenAI instrumentation
-   `withInstrumentedOpenAI()` - Temporary OpenAI instrumentation (TypeScript 5.2+)

## Requirements

-   Node.js 18+ (for native AsyncLocalStorage support)
-   TypeScript 4.5+ (5.2+ for `using` statement support)

## Testing

Run the test suite:

```bash
# Run all tests
pnpm test

# Run tests in watch mode
pnpm test --watch
```

## OpenTelemetry Compatibility

The Atla Insights TypeScript SDK is built on OpenTelemetry standards and is fully compatible with other OpenTelemetry instrumentation

## License

Apache 2.0
