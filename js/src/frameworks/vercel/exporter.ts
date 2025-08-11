import { addOpenInferenceAttributesToSpan } from "@arizeai/openinference-vercel/utils";
import { type ExportResult, ExportResultCode } from "@opentelemetry/core";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
import { OTEL_TRACES_ENDPOINT } from "../../internal/constants.ts";
import {
	applyOpenInferenceInstrumentationName,
	sanitizeAttributes,
} from "../../internal/utils.ts";

interface AtlaVercelExporterOptions {
	token: string;
}

/**
 * Atla Insights SpanExporter for Vercel AI SDK.
 *
 * @example
 * ```typescript
 * // In your app/instrumentation.ts or instrumentation.node.ts file:
 * import { registerOTel } from '@vercel/otel';
 * import { AtlaVercelExporter } from '@atla/insights-sdk';
 *
 * export function register() {
 *   registerOTel({
 *     serviceName: 'my-vercel-app',
 *     traceExporter: new AtlaVercelExporter({
 *       token: process.env.ATLA_API_KEY!,
 *     }),
 *   });
 * }
 *
 * // Then in your app code, use Vercel AI SDK as normal:
 * import { openai } from '@ai-sdk/openai';
 * import { generateText } from 'ai';
 *
 * const result = await generateText({
 *   model: openai('gpt-4-turbo'),
 *   prompt: 'Write a short story about a cat.',
 *   // Enable telemetry to capture traces
 *   experimental_telemetry: { isEnabled: true },
 * });
 * ```
 *
 * @class AtlaVercelExporter
 */
export class AtlaVercelExporter implements SpanExporter {
	private readonly otlpExporter: OTLPTraceExporter;

	constructor(options: AtlaVercelExporterOptions) {
		if (!options.token) {
			throw new Error("Atla token is required.");
		}

		this.otlpExporter = new OTLPTraceExporter({
			url: OTEL_TRACES_ENDPOINT,
			headers: {
				Authorization: `Bearer ${options.token}`,
			},
		});
	}

	export(
		spans: ReadableSpan[],
		resultCallback: (result: ExportResult) => void,
	): void {
		try {
			const processedSpans = spans.map((span) => {
				addOpenInferenceAttributesToSpan(span);
				applyOpenInferenceInstrumentationName(span);
				sanitizeAttributes(span);
				return span;
			});
			this.otlpExporter.export(processedSpans, resultCallback);
		} catch (error) {
			console.error("AtlaVercelExporter: Error processing spans", error);
			resultCallback({
				code: ExportResultCode.FAILED,
			});
		}
	}

	shutdown(): Promise<void> {
		return this.otlpExporter.shutdown();
	}

	forceFlush(): Promise<void> {
		if (this.otlpExporter.forceFlush) {
			return this.otlpExporter.forceFlush();
		}
		return Promise.resolve();
	}
}
