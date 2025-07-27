/**
 * Atla Insights TypeScript SDK
 *
 * A minimal TypeScript SDK for Atla Insights that provides:
 * - Configuration with ATLA_INSIGHTS_TOKEN
 * - Function instrumentation
 * - OpenTelemetry-based tracing
 */

export { configure } from "./main";
export { instrument } from "./instrument";
