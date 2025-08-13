/**
 * @fileoverview Context management utilities for Atla-specific data within OpenTelemetry traces.
 *
 * This module extends OpenTelemetry's context system to store additional metadata
 * that Atla requires but isn't part of the standard OpenInference specification.
 * It provides functions to get, set, and run code within enhanced contexts that
 * carry Atla-specific state alongside standard trace data.
 */
import { context as otelContext, Context, Span } from "@opentelemetry/api";

interface AtlaContext {
	rootSpan?: Span;
	suppressInstrumentation?: boolean;
}

// Store Atla-specific context that isn't part of OpenInference
const atlaContextKey = Symbol("atla.context");

export function getAtlaContext(
	context: Context = otelContext.active(),
): AtlaContext | undefined {
	return context.getValue(atlaContextKey) as AtlaContext | undefined;
}

export function setAtlaContext(
	context: Context,
	atlaContext: AtlaContext,
): Context {
	return context.setValue(atlaContextKey, atlaContext);
}

export function runWithContext<T>(updates: AtlaContext, fn: () => T): T {
	let context = otelContext.active();
	const current = getAtlaContext(context) ?? {};

	// Set Atla specific context
	context = setAtlaContext(context, { ...current, ...updates });
	return otelContext.with(context, fn);
}
