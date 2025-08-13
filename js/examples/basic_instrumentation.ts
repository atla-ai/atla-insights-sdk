/**
 * Basic instrumentation example.
 */
import { diag, DiagConsoleLogger, DiagLogLevel } from "@opentelemetry/api";
diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.DEBUG);

import { configure, instrument, markSuccess, setMetadata } from "../src/index.ts";

async function main(): Promise<void> {
    configure({
        token: process.env.ATLA_INSIGHTS_TOKEN!,
        verbose: true,
        metadata: {
            "project": "my-project",
            "environment": "development",
            "version": "1.0.0",
            "user": "john_doe"
        }
    });

    const myInstrumentedFunction = instrument("My instrumented function")(
        function (): string {
            setMetadata({"function": "function1"});
            const message = "Hello, world!";
            markSuccess();
            return message;
        },
    );

    const myInstrumentedFunction2 = instrument("My instrumented function 2")(
        function (): string {
            setMetadata({"function": "function2"});
            const message = "Hello, world 2!";
            markSuccess();
            return message;
        },
    );

    const result = myInstrumentedFunction();
    console.log("Result:", result);

    myInstrumentedFunction2();
    console.log("Result:", result);

    await new Promise((resolve) => setTimeout(resolve, 1000));
}

main().catch(console.error);
