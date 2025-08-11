import { AtlaVercelExporter } from "@atla/insights-sdk";
import { registerOTel } from "@vercel/otel";

export function register() {
	console.log("registerOTel", process.env.ATLA_API_KEY);
	registerOTel({
		serviceName: "nextjs-openai-simple",
		traceExporter: new AtlaVercelExporter({
			token: process.env.ATLA_API_KEY as string,
		}),
	});
}
