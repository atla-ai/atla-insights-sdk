/**
 * @file providers/openai/index.ts
 * @function instrumentOpenAI
 *
 * Overview
 * -------
 * Thin, provider-native wrapper for the official OpenAI JS client.
 * Adds gen_ai.* attributes and error status to spans around OpenAI calls.
 * Final Atla shaping (atla.*) is performed by frameworks/vercel/AtlaExporter.
 *
 * Public API
 * ----------
 * instrumentOpenAI(client: OpenAI, opts?: InstrumentOpts): OpenAI
 *   - Returns a proxied client with the same surface as the original.
 *
 * Instrumented Endpoints
 * ----------------------
 *   - chat.completions.create (primary)
 *   - (Optional) Responses API analogs if adopted by the application.
 *
 * Span Lifecycle
 * --------------
 *   1) On call:
 *        - Create a span named "gen.openai.chat" (or endpoint-specific).
 *        - Parent to the current active context (respecting upstream tracing).
 *        - Attach request attributes:
 *            gen_ai.system = "openai"
 *            gen_ai.request.model = <request.model>
 *            gen_ai.request.temperature/top_p/max_tokens/penalties (when present)
 *   2) Streaming (if used):
 *        - Optionally emit throttled "token" events with partial deltas.
 *        - Do not aggregate full output here (exporter will handle final shaping).
 *   3) On success:
 *        - gen_ai.response.finish_reason from response.choices[].finish_reason (or equivalent).
 *        - gen_ai.usage.{input_tokens, completion_tokens, total_tokens} if returned.
 *        - Set span status OK.
 *   4) On error:
 *        - Set span status ERROR.
 *        - Attach provider error hints (error.type, error.code, http.status).
 *        - Avoid embedding entire payloads to reduce PII risk.
 *
 * Inputs/Outputs Handling
 * -----------------------
 * This wrapper does not emit atla.input_messages or atla.output_messages. The exporter
 * will synthesize those from Vercel AI attributes if present, or from the raw request/response
 * values exposed by this wrapper via gen_ai.* and ai.* mappings when available.
 *
 * Options
 * -------
 * InstrumentOpts:
 *   - spanName?: string
 *   - captureStreamingDeltas?: boolean (default: false)
 *   - eventThrottleMs?: number (minimum gap between token delta events)
 *
 * Concurrency & Context
 * ---------------------
 *   - Uses @opentelemetry/api to start/activate spans; no provider is created here.
 *   - Respects existing traceparent (from Vercel/Next or user’s own NodeSDK).
 *
 * Dependencies
 * ------------
 *   - openai (official client)
 *   - @opentelemetry/api
 *   - ../../internal/types (for shared types)
 *
 * Testing Notes
 * -------------
 *   - Mock OpenAI client; assert that spans include:
 *       gen_ai.system="openai"
 *       gen_ai.request.model=<model>
 *       finish_reason and usage on success
 *       status=ERROR with lightweight error attributes on failure
 *   - Streaming: verify throttling and end-of-stream behavior.
 */
