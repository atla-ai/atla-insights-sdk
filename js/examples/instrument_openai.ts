/**
 * OpenAI example.
 */
import { diag, DiagConsoleLogger, DiagLogLevel } from "@opentelemetry/api";
diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.DEBUG);

import { configure, instrument, instrumentOpenAI } from "../src/index.ts";

async function main(): Promise<void> {
    configure({
        token: process.env.ATLA_INSIGHTS_TOKEN!,
        metadata: {
            "project": "my-project",
            "environment": "development",
            "version": "1.0.0",
            "user": "john_doe"
        }
    });

    const { default: OpenAI } = await import("openai");
    instrumentOpenAI(OpenAI);

    const client = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY!,
    });

    const myApp = instrument("My GenAI application")(async function(client: any): Promise<void> {
        const completion = await client.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [{ role: "user", content: "Hello, world!" }],
        });

        console.log("Response:", completion.choices[0].message.content);
    });

    await myApp(client);
}

main().catch(console.error);
