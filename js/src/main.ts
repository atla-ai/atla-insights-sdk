/**
 * @fileoverview The main entry point for the Atla Insights SDK.
 *
 * This file contains the main class for the Atla Insights SDK, which is used to
 * configure and use the Atla Insights SDK.
 */
import { trace, type Tracer } from "@opentelemetry/api";
import {
	SimpleSpanProcessor,
	NodeTracerProvider,
	ReadableSpan,
	SpanProcessor,
} from "@opentelemetry/sdk-trace-node";
import {
	type InstrumentationBase,
	registerInstrumentations,
} from "@opentelemetry/instrumentation";
import { ExportResult } from "@opentelemetry/core";
import { Resource } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";
import {
	DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT,
	DEFAULT_SERVICE_NAME,
	OTEL_MODULE_NAME,
	OTEL_TRACES_ENDPOINT,
	METADATA_MARK,
	SUCCESS_MARK,
} from "./internal/constants";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { ConsoleSpanProcessor } from "./console_span_processor";
import { AtlaRootSpanProcessor } from "./atla_root_span_processor";

export interface ConfigurationOptions {
	token: string;
	serviceName?: string;
	verbose?: boolean;
	metadata?: Record<string, string>;
}

class DebugOTLPTraceExporter extends OTLPTraceExporter {
	private verbose: boolean;

	constructor(config: any, verbose: boolean = false) {
		super(config);
		this.verbose = verbose;

		console.log("🔍 [Atla Insights] DebugOTLPTraceExporter constructor");
	}

	export(
		spans: ReadableSpan[],
		resultCallback: (result: ExportResult) => void,
	): void {
		if (this.verbose) {
			console.log(
				`📤 [Atla Insights] Exporting ${spans.length} span(s) to Logfire:`,
			);
			console.log(`   Endpoint: ${this.url}`);

			spans.forEach((span, index) => {
				console.log(`   Span ${index + 1}:`);
				console.log(`     Name: ${span.name}`);
				console.log(`     TraceId: ${span.spanContext().traceId}`);
				console.log(`     SpanId: ${span.spanContext().spanId}`);
				console.log(
					`     Duration: ${span.duration?.[0] || 0}s ${span.duration?.[1] || 0}ns`,
				);
				console.log(`     Attributes:`, span.attributes);
				if (span.resource) {
					console.log(`     Resource:`, span.resource.attributes);
				}
			});
		}

		// Call the original export method with a wrapped callback
		super.export(spans, (result) => {
			if (this.verbose) {
				console.log(`📥 [Atla Insights] Export result:`, {
					code: result.code,
					error: result.error,
				});
			}
			resultCallback(result);
		});
	}
}

class AtlaInsights {
	private tracerProvider?: NodeTracerProvider;
	private tracer?: Tracer;
	private token?: string;
	private serviceName?: string;
	private metadata?: Record<string, string>;
	configured = false;

	private activeInstrumentations = new Map<string, InstrumentationBase[]>();

	/**
	 * Configure the Atla Insights SDK.
	 *
	 * @param options - The configuration options. See {@link ConfigurationOptions}.
	 */
	configure(options: ConfigurationOptions): void {
		const {
			token,
			serviceName = DEFAULT_SERVICE_NAME,
			verbose = false,
			metadata,
		} = options;

		if (!token) {
			throw new Error("Atla Insights: Token is required");
		}

		this.token = token;
		this.serviceName = serviceName;
		this.metadata = metadata;

		// Create resource
		const resource = Resource.default().merge(
			new Resource({
				[ATTR_SERVICE_NAME]: serviceName,
			}),
		);

		// Add Atla exporter
		const atlaExporter = new DebugOTLPTraceExporter(
			{
				url: OTEL_TRACES_ENDPOINT,
				headers: {
					Authorization: `Bearer ${token}`,
				},
			},
			verbose,
		);

		// Update the AtlaRootSpanProcessor instantiation to pass metadata
		const atlaRootProcessor = new AtlaRootSpanProcessor(this.metadata);
		const atlaSpanProcessor = new SimpleSpanProcessor(atlaExporter);
		const spanProcessors: SpanProcessor[] = [
			atlaRootProcessor,
			atlaSpanProcessor,
		];

		if (verbose) {
			spanProcessors.push(new ConsoleSpanProcessor(verbose));
		}

		// Create the tracer provider
		this.tracerProvider = new NodeTracerProvider({
			resource,
			spanLimits: {
				attributeCountLimit: DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT,
			},
			spanProcessors,
		});

		this.tracerProvider.register();
		this.tracer = trace.getTracer(OTEL_MODULE_NAME);
		this.configured = true;

		if (verbose) {
			console.log(
				"🔍 [Atla Insights] Verbose mode enabled - spans will be logged to console",
			);
		}
	}

	getTracer(): Tracer {
		if (!this.tracer) {
			throw new Error("Atla Insights must be configured before use.");
		}
		return this.tracer;
	}

	getTracerProvider(): NodeTracerProvider | undefined {
		return this.tracerProvider;
	}

	getToken(): string {
		return this.token as string;
	}

	getServiceName(): string {
		return this.serviceName as string;
	}

	getMetadata(): Record<string, string> | undefined {
		return this.metadata;
	}

	registerInstrumentations(
		service: string,
		instrumentations: InstrumentationBase[],
	): void {
		// Unregister existing instrumentations for this service if any
		this.unregisterInstrumentations(service);

		// Register new instrumentations
		registerInstrumentations({
			instrumentations,
			tracerProvider: this.tracerProvider,
		});

		// Track them for later unregistration if needed
		this.activeInstrumentations.set(service, instrumentations);
	}

	unregisterInstrumentations(service: string): void {
		const instrumentations = this.activeInstrumentations.get(service);
		if (!instrumentations) {
			return;
		}

		for (const instrumentation of instrumentations) {
			instrumentation.disable();
		}

		this.activeInstrumentations.delete(service);
	}
}

export const ATLA_INSIGHTS = new AtlaInsights();
export const configure = ATLA_INSIGHTS.configure.bind(ATLA_INSIGHTS);
