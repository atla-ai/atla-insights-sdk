/**
 * Nested instrumentation example.
 */
import { diag, DiagConsoleLogger, DiagLogLevel } from "@opentelemetry/api";
diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.DEBUG);

import { configure, instrument } from "../src/index.ts";

async function main(): Promise<void> {
    configure({
        token: process.env.ATLA_INSIGHTS_TOKEN!,
    });

    const myNestedFunction = instrument("My nested function")(function(): string {
        console.log("Inside nested function");
        return "Hello, world!";
    });

    const myInstrumentedFunction = instrument("My instrumented function")(function(): string {
        console.log("Inside main function");
        const result = myNestedFunction();
        return result;
    });

    const result = myInstrumentedFunction();
    console.log("Final result:", result);
}

main().catch(console.error);
