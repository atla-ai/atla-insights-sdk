import { OTEL_MODULE_NAME, OTEL_TRACES_ENDPOINT } from "./constants";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { trace, Tracer } from "@opentelemetry/api";

class AtlaInsights {
    private isShuttingDown = false;
    private sdk: NodeSDK | null = null;
    private tracer: Tracer | null = null;

    public configured = false;

    configure(token: string): void {
        if (this.configured) {
            console.warn("Atla Insights already configured");
            return;
        }

        console.log("🔧 Configuring OpenTelemetry exporter...");
        console.log("📡 Endpoint:", OTEL_TRACES_ENDPOINT);

        const traceExporter = new OTLPTraceExporter({
            url: OTEL_TRACES_ENDPOINT,
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        });

        this.sdk = new NodeSDK({
            traceExporter,
            instrumentations: [],
        });
        this.sdk.start();

        this.tracer = trace.getTracer(OTEL_MODULE_NAME);

        this.configured = true;
        console.info("Atla Insights configured correctly ✅");

        // Add graceful shutdown
        process.on("SIGTERM", () => this.shutdown());
        process.on("SIGINT", () => this.shutdown());
        process.on("beforeExit", () => this.shutdown());
    }

    async shutdown(): Promise<void> {
        if (this.isShuttingDown) return;
        this.isShuttingDown = true;

        if (this.sdk) {
            try {
                await this.sdk.shutdown();
                console.log("✅ OpenTelemetry SDK shut down successfully");
            } catch (error) {
                console.error("❌ Error shutting down OpenTelemetry SDK:", error);
            }
        }
    }

    getTracer(): Tracer {
        if (!this.configured || !this.tracer) {
            throw new Error("Atla Insights must be configured before instrumenting");
        }
        return this.tracer;
    }
}

export const ATLA_INSTANCE = new AtlaInsights();

export const configure = (token: string) => ATLA_INSTANCE.configure(token);

export const shutdown = () => ATLA_INSTANCE.shutdown();
