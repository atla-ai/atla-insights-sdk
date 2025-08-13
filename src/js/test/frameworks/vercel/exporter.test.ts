import type { Attributes } from "@opentelemetry/api";
import { SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { type ExportResult, ExportResultCode } from "@opentelemetry/core";
import { Resource } from "@opentelemetry/resources";
import type { ReadableSpan } from "@opentelemetry/sdk-trace-base";
import { AtlaVercelExporter } from "../../../src/frameworks/vercel/exporter.ts";

// Mock the external dependencies
jest.mock("@arizeai/openinference-vercel/utils", () => ({
	addOpenInferenceAttributesToSpan: jest.fn(),
}));

jest.mock("@opentelemetry/exporter-trace-otlp-http", () => ({
	OTLPTraceExporter: jest.fn().mockImplementation(() => ({
		export: jest.fn(),
		shutdown: jest.fn().mockResolvedValue(undefined),
		forceFlush: jest.fn().mockResolvedValue(undefined),
	})),
}));

jest.mock("../../../src/internal/utils.ts", () => ({
	applyOpenInferenceInstrumentationName: jest.fn(),
	sanitizeAttributes: jest.fn(),
}));

import { addOpenInferenceAttributesToSpan } from "@arizeai/openinference-vercel/utils";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import {
	applyOpenInferenceInstrumentationName,
	sanitizeAttributes,
} from "../../../src/internal/utils.ts";

describe("AtlaVercelExporter", () => {
	const mockToken = "test-token-123";
	let exporter: AtlaVercelExporter;
	let mockOTLPExporter: jest.Mocked<any>;

	const createMockSpan = (
		attributes: Attributes = {},
		name = "test-span",
	): ReadableSpan => ({
		attributes,
		instrumentationLibrary: { name: "ai", version: "1.0.0" },
		name,
		kind: SpanKind.INTERNAL,
		spanContext: () => ({
			traceId: "12345678901234567890123456789012",
			spanId: "1234567890123456",
			traceFlags: 1,
		}),
		startTime: [1640995200, 0],
		endTime: [1640995201, 0],
		events: [],
		links: [],
		status: { code: SpanStatusCode.OK },
		parentSpanId: "0987654321098765",
		droppedAttributesCount: 0,
		droppedEventsCount: 0,
		droppedLinksCount: 0,
		resource: new Resource({ "service.name": "test-service" }),
		duration: [1, 0],
		ended: true,
	});

	beforeEach(() => {
		jest.clearAllMocks();

		mockOTLPExporter = {
			export: jest.fn(),
			shutdown: jest.fn().mockResolvedValue(undefined),
			forceFlush: jest.fn().mockResolvedValue(undefined),
		};

		(OTLPTraceExporter as jest.Mock).mockImplementation(() => mockOTLPExporter);

		exporter = new AtlaVercelExporter({ token: mockToken });
	});

	describe("constructor", () => {
		it("should create an instance with valid token", () => {
			expect(exporter).toBeInstanceOf(AtlaVercelExporter);
			expect(OTLPTraceExporter).toHaveBeenCalledWith({
				url: "https://logfire-eu.pydantic.dev/v1/traces",
				headers: {
					Authorization: `Bearer ${mockToken}`,
				},
			});
		});

		it("should throw error when token is missing", () => {
			expect(() => new AtlaVercelExporter({ token: "" })).toThrow(
				"Atla token is required.",
			);
		});

		it("should throw error when token is undefined", () => {
			expect(() => new AtlaVercelExporter({ token: undefined as any })).toThrow(
				"Atla token is required.",
			);
		});
	});

	describe("export", () => {
		it("should process and export spans successfully", () => {
			const spans = [
				createMockSpan({ "ai.model.provider": "openai" }),
				createMockSpan({ "ai.model.name": "gpt-4" }),
			];
			const resultCallback = jest.fn();

			mockOTLPExporter.export.mockImplementation(
				(_: ReadableSpan[], callback: (result: ExportResult) => void) => {
					callback({ code: ExportResultCode.SUCCESS });
				},
			);

			exporter.export(spans, resultCallback);

			expect(addOpenInferenceAttributesToSpan).toHaveBeenCalledTimes(2);
			expect(applyOpenInferenceInstrumentationName).toHaveBeenCalledTimes(2);
			expect(sanitizeAttributes).toHaveBeenCalledTimes(2);
			expect(mockOTLPExporter.export).toHaveBeenCalledWith(
				spans,
				resultCallback,
			);
			expect(resultCallback).toHaveBeenCalledWith({
				code: ExportResultCode.SUCCESS,
			});
		});

		it("should handle empty spans array", () => {
			const spans: ReadableSpan[] = [];
			const resultCallback = jest.fn();

			mockOTLPExporter.export.mockImplementation(
				(_: ReadableSpan[], callback: (result: ExportResult) => void) => {
					callback({ code: ExportResultCode.SUCCESS });
				},
			);

			exporter.export(spans, resultCallback);

			expect(addOpenInferenceAttributesToSpan).not.toHaveBeenCalled();
			expect(applyOpenInferenceInstrumentationName).not.toHaveBeenCalled();
			expect(sanitizeAttributes).not.toHaveBeenCalled();
			expect(mockOTLPExporter.export).toHaveBeenCalledWith([], resultCallback);
		});

		it("should handle processing errors gracefully", () => {
			const spans = [createMockSpan()];
			const resultCallback = jest.fn();
			const error = new Error("Processing error");

			const originalMock = addOpenInferenceAttributesToSpan as jest.Mock;
			(addOpenInferenceAttributesToSpan as jest.Mock).mockImplementation(() => {
				throw error;
			});

			const consoleSpy = jest.spyOn(console, "error").mockImplementation();

			exporter.export(spans, resultCallback);
			expect(consoleSpy).toHaveBeenCalledWith(
				"AtlaVercelExporter: Error processing spans",
				error,
			);
			expect(resultCallback).toHaveBeenCalledWith({
				code: ExportResultCode.FAILED,
			});
			expect(mockOTLPExporter.export).not.toHaveBeenCalled();

			consoleSpy.mockRestore();
			originalMock.mockClear();
		});

		it("should process spans with complex attributes", () => {
			(applyOpenInferenceInstrumentationName as jest.Mock).mockImplementation(
				jest.fn(),
			);
			(sanitizeAttributes as jest.Mock).mockImplementation(jest.fn());
			(addOpenInferenceAttributesToSpan as jest.Mock).mockImplementation(
				jest.fn(),
			);
			const complexSpan = createMockSpan({
				"ai.model.provider": "openai.gpt-4",
				"ai.prompt.messages": JSON.stringify([
					{ role: "user", content: "Hello world" },
					{ role: "assistant", content: "Hi there!" },
				]),
				"ai.response.finish_reason": "stop",
				"ai.usage.total_tokens": 150,
				"ai.usage.prompt_tokens": 50,
				"ai.usage.completion_tokens": 100,
			});

			const resultCallback = jest.fn();
			mockOTLPExporter.export.mockImplementation(
				(_: ReadableSpan[], callback: (result: ExportResult) => void) => {
					callback({ code: ExportResultCode.SUCCESS });
				},
			);

			exporter.export([complexSpan], resultCallback);

			expect(addOpenInferenceAttributesToSpan).toHaveBeenCalledWith(
				complexSpan,
			);
			expect(applyOpenInferenceInstrumentationName).toHaveBeenCalledWith(
				complexSpan,
			);
			expect(sanitizeAttributes).toHaveBeenCalledWith(complexSpan);
			expect(mockOTLPExporter.export).toHaveBeenCalled();
		});
	});

	describe("shutdown", () => {
		it("should shutdown the underlying OTLP exporter", async () => {
			await exporter.shutdown();
			expect(mockOTLPExporter.shutdown).toHaveBeenCalled();
		});

		it("should handle shutdown errors", async () => {
			const error = new Error("Shutdown error");
			mockOTLPExporter.shutdown.mockRejectedValue(error);
			await expect(exporter.shutdown()).rejects.toThrow("Shutdown error");
		});
	});

	describe("forceFlush", () => {
		it("should force flush the underlying OTLP exporter", async () => {
			await exporter.forceFlush();
			expect(mockOTLPExporter.forceFlush).toHaveBeenCalled();
		});

		it("should handle exporter without forceFlush method", async () => {
			mockOTLPExporter.forceFlush = undefined;
			const result = await exporter.forceFlush();
			expect(result).toBeUndefined();
		});

		it("should handle forceFlush errors", async () => {
			const error = new Error("ForceFlush error");
			mockOTLPExporter.forceFlush.mockRejectedValue(error);
			await expect(exporter.forceFlush()).rejects.toThrow("ForceFlush error");
		});
	});
});
