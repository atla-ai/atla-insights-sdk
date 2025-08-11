import type { ReadableSpan } from "@opentelemetry/sdk-trace-base";

export function sanitizeAttributes(span: ReadableSpan): void {
	const attrs = span.attributes;
	for (const [key, value] of Object.entries(attrs)) {
		if (value == null || value === undefined) {
			delete attrs[key];
		}
	}
}

export function applyOpenInferenceInstrumentationName(
	span: ReadableSpan,
): void {
	if (span.instrumentationLibrary.name !== "ai") return;
	const providerAttribute = span.attributes["ai.model.provider"];
	if (!providerAttribute) return;
	const providerName = String(providerAttribute).split(".")[0];
	if (!providerName) return;
	(span.instrumentationLibrary as { name: string }).name =
		`openinference.instrumentation.${providerName}`;
}
