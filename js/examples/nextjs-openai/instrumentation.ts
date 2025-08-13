import { diag, DiagConsoleLogger, DiagLogLevel } from "@opentelemetry/api";
diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.DEBUG);
import { configure, instrumentVercel } from "@atla/insights-sdk";

export function register() {
    instrumentVercel({
        token: process.env.ATLA_API_KEY!
    });
}
