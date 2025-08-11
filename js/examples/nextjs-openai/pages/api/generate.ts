import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";
import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(
	req: NextApiRequest,
	res: NextApiResponse,
) {
	if (req.method !== "POST") {
		return res.status(405).json({ error: "Method not allowed" });
	}

	try {
		const result = await generateText({
			model: openai("gpt-4o-mini"),
			prompt: "Write a short haiku about observability.",
			experimental_telemetry: { isEnabled: true },
		});

		return res.json({ text: result.text });
	} catch (error) {
		console.error("Error generating text:", error);
		return res.status(500).json({ error: "Failed to generate text" });
	}
}
