// Core configuration
export { configure, type ConfigurationOptions } from "./main.ts";

// Instrumentation
export { instrument } from "./instrumentation.ts";

// Manual span creation
export { startAsCurrentSpan, AtlaSpan } from "./span.ts";

// Metadata management
export { setMetadata, getMetadata, withMetadata, clearMetadata } from "./metadata.ts";

// Marking functionality
export { markSuccess, markFailure } from "./marking.ts";

// LLM provider instrumentation
export {
    instrumentOpenAI,
    uninstrumentOpenAI,
    withInstrumentedOpenAI,
} from "./providers/openai/index.ts";
