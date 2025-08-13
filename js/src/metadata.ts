/**
 * Metadata management for Atla Insights.
 * Works with both configure() and instrumentVercel() approaches.
 */
import { trace, context as otelContext } from "@opentelemetry/api";
import { METADATA_MARK } from "./internal/constants";

const METADATA_CONTEXT_KEY = Symbol("atla.metadata");

// Metadata validation limits (matching Python SDK)
const MAX_METADATA_FIELDS = 25;
const MAX_METADATA_KEY_CHARS = 40;
const MAX_METADATA_VALUE_CHARS = 100;

/**
 * Truncate a string value to the specified maximum length.
 */
function truncateValue(value: string, maxLength: number): string {
    return value.length > maxLength ? value.substring(0, maxLength) : value;
}

/**
 * Validate the user-provided metadata field.
 * Mirrors the Python SDK's _validate_metadata function.
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
 * Set metadata that will be added to all spans in the current trace.
 * This is for runtime metadata updates within a trace.
 */
export function setMetadata(metadata: Record<string, string>): void {
    const span = trace.getActiveSpan();
    if (span) {
        const validatedMetadata = validateMetadata(metadata);

        // Get existing metadata from the span if any
        const existingMetadata = span.attributes[METADATA_MARK];
        let currentMetadata: Record<string, string> = {};

        if (existingMetadata && typeof existingMetadata === 'string') {
            try {
                currentMetadata = JSON.parse(existingMetadata);
            } catch (e) {
                // Ignore parse errors
            }
        }

        // Merge with new metadata
        const mergedMetadata = { ...currentMetadata, ...validatedMetadata };
        span.setAttribute(METADATA_MARK, JSON.stringify(mergedMetadata));
    }
}

/**
 * Get current metadata from the active span.
 */
export function getMetadata(): Record<string, string> | undefined {
    const span = trace.getActiveSpan();
    if (span) {
        const metadataAttr = span.attributes[METADATA_MARK];
        if (metadataAttr && typeof metadataAttr === 'string') {
            try {
                return JSON.parse(metadataAttr);
            } catch (e) {
                // Ignore parse errors
            }
        }
    }
    return undefined;
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
    const currentMetadata = ctx.getValue(METADATA_CONTEXT_KEY) as Record<string, string> || {};
    const newCtx = ctx.setValue(METADATA_CONTEXT_KEY, { ...currentMetadata, ...validatedMetadata });

    return otelContext.with(newCtx, fn);
}

/**
 * Clear all metadata from the active span.
 */
export function clearMetadata(): void {
    const span = trace.getActiveSpan();
    if (span) {
        span.setAttribute(METADATA_MARK, "{}");
    }
}
