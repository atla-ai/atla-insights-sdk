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
	type SpanProcessor,
} from "@opentelemetry/sdk-trace-node";
import {
	type InstrumentationBase,
	registerInstrumentations,
} from "@opentelemetry/instrumentation";
import { Resource } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";
import {
	DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT,
	DEFAULT_SERVICE_NAME,
	OTEL_MODULE_NAME,
	OTEL_TRACES_ENDPOINT,
} from "./internal/constants";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { AtlaRootSpanProcessor } from "./atla_root_span_processor";
import { setGlobalMetadata } from "./metadata";

export interface ConfigurationOptions {
	token: string;
	serviceName?: string;
	metadata?: Record<string, string>;
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
		const { token, serviceName = DEFAULT_SERVICE_NAME, metadata } = options;

		if (!token) {
			throw new Error("Atla Insights: Token is required");
		}

		this.token = token;
		this.serviceName = serviceName;
		this.metadata = metadata;

		// Set global metadata
		if (metadata) {
			setGlobalMetadata(metadata);
		}

		// Create resource
		const resource = Resource.default().merge(
			new Resource({
				[ATTR_SERVICE_NAME]: serviceName,
			}),
		);

		// Add Atla exporter
		const atlaExporter = new OTLPTraceExporter({
			url: OTEL_TRACES_ENDPOINT,
			headers: {
				Authorization: `Bearer ${token}`,
			},
		});

		// Update the AtlaRootSpanProcessor instantiation to pass metadata
		const atlaRootProcessor = new AtlaRootSpanProcessor(this.metadata);
		const atlaSpanProcessor = new SimpleSpanProcessor(atlaExporter);
		const spanProcessors: SpanProcessor[] = [
			atlaRootProcessor,
			atlaSpanProcessor,
		];

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
