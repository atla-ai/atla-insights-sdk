/**
 * @fileoverview Instrumentation utilities for Atla Insights.
 *
 * This module provides decorators to instrument functions with Atla Insights.
 */

/** biome-ignore-all lint/suspicious/noExplicitAny: We need to support any function */
import { getAtlaContext, runWithContext } from "./context";
import { ATLA_INSIGHTS } from "./main";

type AsyncFunction<T extends any[], R> = (...args: T) => Promise<R>;
type SyncFunction<T extends any[], R> = (...args: T) => R;
type AnyFunction = AsyncFunction<any, any> | SyncFunction<any, any>;

export function instrument(nameOrTarget: string | AnyFunction): any {
	// Used as @instrument without arguments
	if (typeof nameOrTarget === "function") {
		return instrumentFunction(nameOrTarget, nameOrTarget.name || "anonymous");
	}

	// Used as @instrument("custom name")
	return (target: AnyFunction) => instrumentFunction(target, nameOrTarget);
}

function instrumentFunction<T extends AnyFunction>(fn: T, spanName: string): T {
	const tracer = ATLA_INSIGHTS.getTracer();

	// Instrument async function
	if (
		fn.constructor.name === "AsyncFunction" ||
		fn.constructor.name === "GeneratorFunction"
	) {
		return async function instrumentedAsync(...args: any[]) {
			const context = getAtlaContext();
			// If suppressInstrumentation is set, we don't want to instrument the function
			if (context?.suppressInstrumentation) {
				return await fn(...args);
			}

			return tracer.startActiveSpan(spanName, async (span) => {
				try {
					// Run with the updated context
					return await runWithContext(
						{
							...context,
							rootSpan: context?.rootSpan ?? span,
						},
						async () => await fn(...args),
					);
				} catch (error) {
					span.recordException(error as Error);
					throw error;
				} finally {
					span.end();
				}
			});
		} as T;
	}

	// Instrument sync function
	return function instrumentedSync(...args: any[]) {
		const context = getAtlaContext();

		// If suppressInstrumentation is set, we don't want to instrument the function
		if (context?.suppressInstrumentation) {
			return fn(...args);
		}

		return tracer.startActiveSpan(spanName, (span) => {
			try {
				// Run with the updated context
				return runWithContext(
					{
						...context,
						rootSpan: context?.rootSpan ?? span,
					},
					() => fn(...args),
				);
			} catch (error) {
				span.recordException(error as Error);
				throw error;
			} finally {
				span.end();
			}
		});
	} as T;
}
