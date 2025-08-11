import type { Attributes, AttributeValue } from "@opentelemetry/api";
import { SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { Resource } from "@opentelemetry/resources";
import type { ReadableSpan } from "@opentelemetry/sdk-trace-base";
import {
	applyOpenInferenceInstrumentationName,
	sanitizeAttributes,
} from "../../src/internal/utils.ts";

describe("utils", () => {
	const makeSpan = (attrs: Attributes, name = "ai"): ReadableSpan => {
		return {
			attributes: attrs as Attributes,
			instrumentationLibrary: { name },
			name,
			kind: SpanKind.INTERNAL,
			spanContext: () => ({
				traceId: "xxx-yyy-zzz",
				spanId: "xxx-yyy-zzz",
				traceFlags: 0,
			}),
			startTime: [0, 0],
			endTime: [0, 0],
			events: [],
			links: [],
			status: { code: SpanStatusCode.OK },
			parentSpanId: "xxx-yyy-zzz",
			droppedAttributesCount: 0,
			droppedEventsCount: 0,
			droppedLinksCount: 0,
			resource: new Resource({}),
			duration: [0, 0],
			ended: false,
		};
	};

	describe("sanitizeAttributes", () => {
		it("removes null and undefined, keeps other falsy values", () => {
			const span = makeSpan({
				a: undefined,
				b: null as unknown as AttributeValue,
				c: [null, undefined, 0, "", false, "x"] as AttributeValue,
				d: 0 as AttributeValue,
				e: "" as AttributeValue,
				f: false as AttributeValue,
				g: "x" as AttributeValue,
			});
			sanitizeAttributes(span);
			expect(span.attributes).toEqual({
				c: [null, undefined, 0, "", false, "x"],
				d: 0,
				e: "",
				f: false,
				g: "x",
			});
		});
	});

	describe("applyOpenInferenceInstrumentationName", () => {
		it("does nothing when instrumentationLibrary.name is not 'ai'", () => {
			const span = makeSpan({ "ai.model.provider": "openai.gpt-4o" }, "not-ai");
			applyOpenInferenceInstrumentationName(span);
			expect(span.instrumentationLibrary.name).toBe("not-ai");
		});

		it("does nothing when provider attribute is missing", () => {
			const span = makeSpan({});
			applyOpenInferenceInstrumentationName(span);
			expect(span.instrumentationLibrary.name).toBe("ai");
		});

		it("sets name from provider prefix before first dot", () => {
			const span = makeSpan({ "ai.model.provider": "openai.gpt-4o" });
			applyOpenInferenceInstrumentationName(span);
			expect(span.instrumentationLibrary.name).toBe(
				"openinference.instrumentation.openai",
			);
		});

		it("handles provider without dot", () => {
			const span = makeSpan({ "ai.model.provider": "anthropic" });
			applyOpenInferenceInstrumentationName(span);
			expect(span.instrumentationLibrary.name).toBe(
				"openinference.instrumentation.anthropic",
			);
		});

		it("ignores empty provider", () => {
			const span = makeSpan({ "ai.model.provider": "" });
			applyOpenInferenceInstrumentationName(span);
			expect(span.instrumentationLibrary.name).toBe("ai");
		});
	});
});
