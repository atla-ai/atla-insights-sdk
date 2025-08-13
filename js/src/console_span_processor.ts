import { ReadableSpan, SpanProcessor } from "@opentelemetry/sdk-trace-base";

/**
 * A simple console span processor for debugging purposes.
 * This will print span information to the console when spans are ended.
 */
export class ConsoleSpanProcessor implements SpanProcessor {
    private verbose: boolean;

    constructor(verbose: boolean = false) {
        this.verbose = verbose;
    }

    onStart(span: ReadableSpan): void {
        // Optional: log when spans start
    }

    onEnd(span: ReadableSpan): void {
        const duration = span.endTime && span.startTime
            ? (span.endTime[0] - span.startTime[0]) * 1000 + (span.endTime[1] - span.startTime[1]) / 1000000
            : 0;

        console.log(`🔍 [Atla Insights] Span: ${span.name} (${duration.toFixed(2)}ms)`);

        if (this.verbose) {
            console.log(`   TraceId: ${span.spanContext().traceId}`);
            console.log(`   SpanId: ${span.spanContext().spanId}`);
            console.log(`   ParentSpanId: ${span.parentSpanId || 'none'}`);
            console.log(`   Status: ${span.status.code} ${span.status.message || ''}`);
        }

        if (span.attributes && Object.keys(span.attributes).length > 0) {
            console.log(`   Attributes:`, span.attributes);
        }

        if (span.events && span.events.length > 0) {
            console.log(`   Events:`, span.events.length);
            if (this.verbose) {
                span.events.forEach((event, i) => {
                    console.log(`     Event ${i + 1}: ${event.name}`, event.attributes);
                });
            }
        }

        if (this.verbose && span.resource) {
            console.log(`   Resource:`, span.resource.attributes);
        }
    }

    shutdown(): Promise<void> {
        return Promise.resolve();
    }

    forceFlush(): Promise<void> {
        return Promise.resolve();
    }
}
