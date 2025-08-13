import { ReadableSpan, Span, SpanProcessor } from "@opentelemetry/sdk-trace-base";
import { Context } from "@opentelemetry/api";
import { METADATA_MARK, SUCCESS_MARK } from "./internal/constants";

export class AtlaRootSpanProcessor implements SpanProcessor {
    constructor(private metadata?: Record<string, string>) {}

    onStart(span: Span, parentContext?: Context): void {
        if (span.parentSpanId) {
            return;
        }

        // This is a root span
        span.setAttribute(SUCCESS_MARK, -1);

        if (this.metadata && Object.keys(this.metadata).length > 0) {
            span.setAttribute(METADATA_MARK, JSON.stringify(this.metadata));
        }
    }

    onEnd(span: ReadableSpan): void {
        // No processing needed on end
    }

    shutdown(): Promise<void> {
        return Promise.resolve();
    }

    forceFlush(): Promise<void> {
        return Promise.resolve();
    }
}
