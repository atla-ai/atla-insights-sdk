/**
 * Metadata management for Atla Insights.
 */
import { trace, context as otelContext } from "@opentelemetry/api";
import { METADATA_MARK, MAX_METADATA_FIELDS, MAX_METADATA_KEY_CHARS, MAX_METADATA_VALUE_CHARS } from "./internal/constants";

const METADATA_CONTEXT_KEY = Symbol("atla.metadata");

// Global metadata storage
let globalMetadata: Record<string, string> = {};

/**
 * Truncate a string value to the specified maximum length.
 */
function truncateValue(value: string, maxLength: number): string {
    return value.length > maxLength ? value.substring(0, maxLength) : value;
}

/**
 * Validate the user-provided metadata field.
 */
function validateMetadata(metadata: Record<string, string>): Record<string, string> {
    if (typeof metadata !== 'object' || metadata === null || Array.isArray(metadata)) {
        throw new Error("The metadata field must be a dictionary.");
    }

    // Verify all keys and values are strings
    for (const [key, value] of Object.entries(metadata)) {
        if (typeof key !== 'string' || typeof value !== 'string') {
            console.error("The metadata field must be a mapping of string to string.");
            // Convert non-strings to strings as fallback
            const stringKey = String(key);
            const stringValue = String(value);
            metadata = { ...metadata };
            delete metadata[key];
            metadata[stringKey] = stringValue;
        }
    }

    // Limit number of fields
    if (Object.keys(metadata).length > MAX_METADATA_FIELDS) {
        console.error(
            `The metadata field has ${Object.keys(metadata).length} fields, ` +
            `but the maximum is ${MAX_METADATA_FIELDS}.`
        );
        const entries = Object.entries(metadata).slice(0, MAX_METADATA_FIELDS);
        metadata = Object.fromEntries(entries);
    }

    // Truncate oversized keys
    const oversizedKeys = Object.keys(metadata).filter(k => k.length > MAX_METADATA_KEY_CHARS);
    if (oversizedKeys.length > 0) {
        console.error(
            `The metadata field must have keys with less than ${MAX_METADATA_KEY_CHARS} characters.`
        );
        const newMetadata: Record<string, string> = {};
        for (const [key, value] of Object.entries(metadata)) {
            const truncatedKey = truncateValue(key, MAX_METADATA_KEY_CHARS);
            newMetadata[truncatedKey] = value;
        }
        metadata = newMetadata;
    }

    // Truncate oversized values
    const oversizedValues = Object.values(metadata).filter(v => v.length > MAX_METADATA_VALUE_CHARS);
    if (oversizedValues.length > 0) {
        console.error(
            `The metadata field must have values with less than ${MAX_METADATA_VALUE_CHARS} characters.`
        );
        for (const [key, value] of Object.entries(metadata)) {
            if (value.length > MAX_METADATA_VALUE_CHARS) {
                metadata[key] = truncateValue(value, MAX_METADATA_VALUE_CHARS);
            }
        }
    }

    return metadata;
}

/**
 * Set global metadata (called internally during configuration).
 */
export function setGlobalMetadata(metadata: Record<string, string>): void {
    globalMetadata = validateMetadata(metadata || {});
}

/**
 * Set metadata that will be added to all spans in the current trace.
 * This is for runtime metadata updates within a trace.
 */
export function setMetadata(metadata: Record<string, string>): void {
    const span = trace.getActiveSpan();
    if (span) {
        const validatedMetadata = validateMetadata(metadata);

        // Merge with global metadata
        const currentMetadata = getMetadata() || {};
        const mergedMetadata = { ...currentMetadata, ...validatedMetadata };

        const context = otelContext.active();
        const newContext = context.setValue(METADATA_CONTEXT_KEY, mergedMetadata);
        otelContext.with(newContext, () => {
            span.setAttribute(METADATA_MARK, JSON.stringify(mergedMetadata));
        });
    }
}

/**
 * Get current metadata using fallback pattern.
 */
export function getMetadata(): Record<string, string> | undefined {
    const context = otelContext.active();
    const contextMetadata = context.getValue(METADATA_CONTEXT_KEY) as Record<string, string>;
    return contextMetadata || globalMetadata || undefined;
}

/**
 * Run a function with additional metadata in context.
 */
export function withMetadata<T>(
    metadata: Record<string, string>,
    fn: () => T | Promise<T>
): T | Promise<T> {
    const validatedMetadata = validateMetadata(metadata);
    const ctx = otelContext.active();
    const newCtx = ctx.setValue(METADATA_CONTEXT_KEY, validatedMetadata);
    return otelContext.with(newCtx, fn);
}

/**
 * Clear runtime metadata from context.
 */
export function clearMetadata(): void {
    const span = trace.getActiveSpan();
    if (span) {
        const ctx = otelContext.active();
        const newCtx = ctx.setValue(METADATA_CONTEXT_KEY, undefined);
        otelContext.with(newCtx, () => {
            span.setAttribute(METADATA_MARK, JSON.stringify(globalMetadata || {}));
        });
    }
}
