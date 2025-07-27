import { Span, SpanStatusCode } from "@opentelemetry/api";
import { ATLA_INSTANCE } from "./main";

/**
 * Instruments a function with OpenTelemetry tracing
 * @param fn The function to instrument
 * @param spanName Optional custom span name, defaults to function name
 */
export function instrument<T extends (...args: any[]) => any>(fn: T, name?: string): T {
    const spanName = name || fn.name || "Unnamed Span";

    return ((...args: Parameters<T>): ReturnType<T> => {
        if (!ATLA_INSTANCE.configured) {
            console.error("Atla Insights not configured, skipping instrumentation");
            return fn(...args);
        }
        const tracer = ATLA_INSTANCE.getTracer();
        return tracer.startActiveSpan(spanName, (span: Span) => {
            try {
                const result = fn(...args);

                // Handle async functions
                if (result && typeof result.then === "function") {
                    return result
                        .then((value: any) => {
                            span.setStatus({ code: SpanStatusCode.OK });
                            span.end();
                            return value;
                        })
                        .catch((error: any) => {
                            span.recordException(error);
                            span.setStatus({
                                code: SpanStatusCode.ERROR,
                                message: error.message,
                            });
                            span.end();
                            throw error;
                        }) as ReturnType<T>;
                }

                // Handle sync functions
                span.setStatus({ code: SpanStatusCode.OK });
                span.end();
                return result;
            } catch (error: any) {
                span.recordException(error);
                span.setStatus({
                    code: SpanStatusCode.ERROR,
                    message: error.message,
                });
                span.end();
                throw error;
            }
        });
    }) as T;
}
