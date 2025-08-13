/**
 * Marking functionality for Atla Insights.
 * Marks the root span of the current trace as success/failure.
 */
import { SUCCESS_MARK } from "./internal/constants";
import { getAtlaContext } from "./context";

/**
 * Mark the root span with a value.
 */
function markRootSpan(value: 0 | 1): void {
    const context = getAtlaContext();
    const rootSpan = context?.rootSpan;

    if (!rootSpan) {
        throw new Error("Atla marking can only be done within an instrumented function.");
    }

    rootSpan.setAttribute(SUCCESS_MARK, value);
}

/**
 * Mark the root span in the current trace as successful.
 *
 * This function should only be called within an instrumented function.
 *
 * ```typescript
 * import { instrument, markSuccess } from "@atla-insights/core";
 *
 * const myFunction = instrument("My Function")(
 *   function(): string {
 *     markSuccess();
 *     return "success ✅";
 *   }
 * );
 * ```
 */
export function markSuccess(): void {
    markRootSpan(1);
}

/**
 * Mark the root span in the current trace as failed.
 *
 * This function should only be called within an instrumented function.
 *
 * ```typescript
 * import { instrument, markFailure } from "@atla-insights/core";
 *
 * const myFunction = instrument("My Function")(
 *   function(): string {
 *     markFailure();
 *     return "failure ❌";
 *   }
 * );
 * ```
 */
export function markFailure(): void {
    markRootSpan(0);
}
