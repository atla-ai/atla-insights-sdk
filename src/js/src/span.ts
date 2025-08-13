import { Span, SpanKind } from "@opentelemetry/api";
import type {
	ChatCompletionMessageParam,
	ChatCompletionAssistantMessageParam,
	ChatCompletionFunctionTool,
} from "openai/resources/chat/completions";
import {
	SemanticConventions,
	OpenInferenceSpanKind,
	MimeType,
	MESSAGE_ROLE,
	MESSAGE_CONTENT,
	MESSAGE_TOOL_CALLS,
	TOOL_CALL_FUNCTION_NAME,
	TOOL_CALL_FUNCTION_ARGUMENTS_JSON,
	MESSAGE_TOOL_CALL_ID,
	MESSAGE_NAME,
	MESSAGE_FUNCTION_CALL_NAME,
	MESSAGE_FUNCTION_CALL_ARGUMENTS_JSON,
	TOOL_JSON_SCHEMA,
} from "@arizeai/openinference-semantic-conventions";
import { ATLA_INSIGHTS } from "./main";
import { getAtlaContext, runWithContext } from "./context";

export class AtlaSpan {
	constructor(private span: Span) {}

	recordGeneration(params: {
		inputMessages: ChatCompletionMessageParam[];
		outputMessages: ChatCompletionAssistantMessageParam[];
		tools?: ChatCompletionFunctionTool[];
	}): void {
		const { inputMessages, outputMessages, tools } = params;

		this.span.setAttribute(
			SemanticConventions.OPENINFERENCE_SPAN_KIND,
			OpenInferenceSpanKind.LLM,
		);

		// Record input messages
		this.span.setAttribute(
			SemanticConventions.INPUT_VALUE,
			JSON.stringify(inputMessages),
		);
		this.span.setAttribute(SemanticConventions.INPUT_MIME_TYPE, MimeType.JSON);
		this._setMessageAttributes(
			SemanticConventions.LLM_INPUT_MESSAGES,
			inputMessages,
		);

		// Record output messages
		this.span.setAttribute(
			SemanticConventions.OUTPUT_VALUE,
			JSON.stringify(outputMessages),
		);
		this.span.setAttribute(SemanticConventions.OUTPUT_MIME_TYPE, MimeType.JSON);
		this._setMessageAttributes(
			SemanticConventions.LLM_OUTPUT_MESSAGES,
			outputMessages,
		);

		// Set tools if provided
		if (tools && tools.length > 0) {
			tools.forEach((tool, toolIndex) => {
				const toolPrefix = `${SemanticConventions.LLM_TOOLS}.${toolIndex}`;
				this.span.setAttribute(
					`${toolPrefix}.${TOOL_JSON_SCHEMA}`,
					JSON.stringify(tool),
				);
			});
		}
	}

	private _setMessageAttributes(
		prefix: string,
		messages:
			| ChatCompletionMessageParam[]
			| ChatCompletionAssistantMessageParam[],
	): void {
		messages.forEach((message, index) => {
			const messagePrefix = `${prefix}.${index}`;

			// Record message role
			this.span.setAttribute(`${messagePrefix}.${MESSAGE_ROLE}`, message.role);

			// Record message content
			if (message.content) {
				if (typeof message.content === "string") {
					this.span.setAttribute(
						`${messagePrefix}.${MESSAGE_CONTENT}`,
						message.content,
					);
				} else if (Array.isArray(message.content)) {
					const textContent = message.content
						.filter((part) => part.type === "text" && "text" in part)
						.map((part) => (part as { text: string }).text)
						.join("\n");
					this.span.setAttribute(
						`${messagePrefix}.${MESSAGE_CONTENT}`,
						textContent,
					);
				}
			}

			// Record message tool calls
			if ("tool_calls" in message && message.tool_calls) {
				message.tool_calls.forEach((toolCall, toolIndex) => {
					const toolCallPrefix = `${messagePrefix}.${MESSAGE_TOOL_CALLS}.${toolIndex}`;
					if ("function" in toolCall && toolCall.function) {
						this.span.setAttribute(
							`${toolCallPrefix}.${TOOL_CALL_FUNCTION_NAME}`,
							toolCall.function.name,
						);
						this.span.setAttribute(
							`${toolCallPrefix}.${TOOL_CALL_FUNCTION_ARGUMENTS_JSON}`,
							toolCall.function.arguments,
						);
					}
				});
			}

			// Set other message attributes
			if ("tool_call_id" in message && message.tool_call_id) {
				this.span.setAttribute(
					`${messagePrefix}.${MESSAGE_TOOL_CALL_ID}`,
					message.tool_call_id,
				);
			}

			if ("name" in message && message.name) {
				this.span.setAttribute(
					`${messagePrefix}.${MESSAGE_NAME}`,
					message.name,
				);
			}

			if ("function_call" in message && message.function_call) {
				this.span.setAttribute(
					`${messagePrefix}.${MESSAGE_FUNCTION_CALL_NAME}`,
					message.function_call.name,
				);
				this.span.setAttribute(
					`${messagePrefix}.${MESSAGE_FUNCTION_CALL_ARGUMENTS_JSON}`,
					message.function_call.arguments,
				);
			}
		});
	}

	// biome-ignore lint/suspicious/noExplicitAny: Allow any value
	setAttribute(key: string, value: any): this {
		this.span.setAttribute(key, value);
		return this;
	}

	// biome-ignore lint/suspicious/noExplicitAny: Allow any value
	setStatus(status: any): this {
		this.span.setStatus(status);
		return this;
	}

	recordException(exception: Error): void {
		this.span.recordException(exception);
	}

	// biome-ignore lint/suspicious/noExplicitAny: Allow any value
	end(endTime?: any): void {
		this.span.end(endTime);
	}
}

/**
 * Start a span as the current span and run the given function.
 *
 * @param name - The name of the span.
 * @param fn - The function to run. The function will be run with the current context.
 * @returns The result of the function.
 */
export async function startAsCurrentSpan<T>(
	name: string,
	fn: (span: AtlaSpan) => T | Promise<T>,
): Promise<T> {
	const tracer = ATLA_INSIGHTS.getTracer();

	return tracer.startActiveSpan(
		name,
		{ kind: SpanKind.INTERNAL },
		async (span) => {
			const atlaSpan = new AtlaSpan(span);
			const currentContext = getAtlaContext();

			try {
				return await runWithContext(
					{
						...currentContext,
						rootSpan: currentContext?.rootSpan ?? span,
					},
					async () => await fn(atlaSpan),
				);
			} finally {
				span.end();
			}
		},
	);
}
