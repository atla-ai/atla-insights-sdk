import { OpenAIInstrumentation } from "@arizeai/openinference-instrumentation-openai";
import { getAtlaContext } from "../../context";
import { ATLA_INSIGHTS } from "../../main";

const SERVICE_NAME = "openai";

let openAIInstrumentation: OpenAIInstrumentation | null = null;

/**
 * Instrument the OpenAI LLM provider.
 *
 * This function enables tracing for all OpenAI API calls made through
 * the official OpenAI JavaScript/TypeScript client.
 *
 * @example
 * ```typescript
 * import { configure, instrumentOpenAI } from "@atla/insights-sdk";
 * import OpenAI from "openai";
 *
 * // Configure Atla Insights first
 * configure({
 *   token: process.env.ATLA_API_KEY!,
 * });
 *
 * // Enable OpenAI instrumentation
 * instrumentOpenAI();
 *
 * // Use OpenAI as normal - it will be automatically traced
 * const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
 * const completion = await openai.chat.completions.create({
 *   model: "gpt-4",
 *   messages: [{ role: "user", content: "Hello!" }],
 * });
 * ```
 *
 * @param openaiModule - The OpenAI module to instrument. If not provided, the default OpenAI module will be instrumented.
 *
 * @example
 * ```typescript
 * import { configure, instrumentOpenAI } from "@atla/insights-sdk";
 * import OpenAI from "openai";
 *
 * // Configure Atla Insights first
 * configure({ token: process.env.ATLA_API_KEY! });
 *
 * // Manually instrument the OpenAI module
 * instrumentOpenAI(OpenAI);
 *
 * // Use OpenAI as normal - it will be automatically traced
 * const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
 * const completion = await openai.chat.completions.create({
 *   model: "gpt-4",
 *   messages: [{ role: "user", content: "Hello!" }],
 * });
 * ```
 *
 * @returns void
 */
export function instrumentOpenAI(openaiModule?: any): void {
    const context = getAtlaContext();
    if (context?.suppressInstrumentation) {
        return;
    }

    if (!ATLA_INSIGHTS.configured) {
        throw new Error(
            "Atla Insights must be configured before instrumenting OpenAI. " +
                "Please call configure first.",
        );
    }

    openAIInstrumentation = new OpenAIInstrumentation({
        tracerProvider: ATLA_INSIGHTS.getTracerProvider(),
    });

    // If a module is provided, manually instrument it
    if (openaiModule) {
        openAIInstrumentation.manuallyInstrument(openaiModule);
    }

    // Register it with OpenTelemetry
    ATLA_INSIGHTS.registerInstrumentations(SERVICE_NAME, [openAIInstrumentation]);
}

/**
 * Uninstrument the OpenAI LLM provider.
 *
 * This function disables tracing for OpenAI API calls.
 *
 * @example
 * ```typescript
 * import { uninstrumentOpenAI } from "@atla/insights-sdk";
 *
 * // Disable OpenAI instrumentation
 * uninstrumentOpenAI();
 * ```
 *
 * @returns void
 */
export function uninstrumentOpenAI(): void {
    const context = getAtlaContext();
    if (context?.suppressInstrumentation) {
        return;
    }

    ATLA_INSIGHTS.unregisterInstrumentations(SERVICE_NAME);
}

/**
 * Create a disposable OpenAI instrumentation resource.
 *
 * This function enables OpenAI instrumentation and returns a disposable resource
 * that automatically disables instrumentation when disposed. This is particularly
 * useful with TypeScript's `using` statement for automatic resource management.
 *
 * @example
 * ```typescript
 * import { withInstrumentedOpenAI } from "@atla/insights-sdk";
 * import OpenAI from "openai";
 *
 * // Use with using statement (requires TypeScript 5.2+)
 * {
 *   using instrumented = withInstrumentedOpenAI();
 *   const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
 *   // OpenAI calls here will be traced
 * }
 * // OpenAI instrumentation automatically disabled here
 *
 * // Or manually manage lifecycle
 * const instrumented = withInstrumentedOpenAI();
 * try {
 *   const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
 *   // OpenAI calls here will be traced
 * } finally {
 *   instrumented[Symbol.dispose]();
 * }
 * ```
 *
 * @returns A disposable resource that cleans up OpenAI instrumentation when disposed
 */
export function withInstrumentedOpenAI(): Disposable {
    instrumentOpenAI();

    return {
        [Symbol.dispose]() {
            uninstrumentOpenAI();
        },
    };
}
