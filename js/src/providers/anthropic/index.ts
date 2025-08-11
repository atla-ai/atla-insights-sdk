/**
 * @file providers/anthropic/index.ts
 * @function instrumentAnthropic
 *
 * Overview
 * -------
 * Thin wrapper for Anthropic Messages API that records provider-native gen_ai.* attributes.
 * Final Atla shaping (OpenAI-compatible messages/tools) is performed by frameworks/vercel/AtlaExporter.
 *
 * Public API
 * ----------
 * instrumentAnthropic(client: Anthropic, opts?: InstrumentOpts): Anthropic
 *   - Returns a proxied client with the same surface as the original.
 *
 * Instrumented Endpoints
 * ----------------------
 *   - messages.create (primary)
 *   - Streaming variants (if the app uses them)
 *
 * Span Lifecycle
 * --------------
 *   1) On call:
 *        - Start span "gen.anthropic.messages" (parented to active context).
 *        - Attach request attributes:
 *            gen_ai.system = "anthropic"
 *            gen_ai.request.model = <request.model>
 *            gen_ai.request.temperature/top_p/top_k/max_tokens (when present)
 *   2) Streaming:
 *        - Optionally emit throttled "token" events as deltas arrive.
 *   3) On success:
 *        - gen_ai.response.finish_reason from stop_reason
 *        - gen_ai.usage.{input_tokens, output_tokens} if returned
 *        - status OK
 *   4) On error:
 *        - status ERROR with provider error code/type/http status (lightweight only)
 *
 * Inputs/Outputs Handling
 * -----------------------
 * This wrapper does not serialize full messages. The exporter will:
 *   - Normalize Anthropic content parts (system + user messages) into OpenAI Chat format,
 *   - Map tool_use/tool_result to atla.tools / atla.tool_calls,
 *   - Apply privacy and field truncation.
 *
 * Options
 * -------
 * InstrumentOpts:
 *   - spanName?: string
 *   - captureStreamingDeltas?: boolean (default: false)
 *   - eventThrottleMs?: number
 *
 * Dependencies
 * ------------
 *   - @anthropic-ai/sdk
 *   - @opentelemetry/api
 *   - ../../internal/types
 *
 * Testing Notes
 * -------------
 *   - Mock client: verify gen_ai.system/model set, stop_reason mapped, usage recorded.
 *   - Error path: status ERROR and minimal error attributes.
 *   - Streaming: correct event throttling and closure.
 */
