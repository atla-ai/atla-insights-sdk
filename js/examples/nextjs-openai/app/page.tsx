"use client";

import { useState } from "react";

export default function Page() {
	const [text, setText] = useState<string>("");
	const [loading, setLoading] = useState(false);

	const generateText = async () => {
		setLoading(true);
		try {
			const response = await fetch("/api/generate", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
			});

			if (!response.ok) {
				throw new Error("Failed to generate text");
			}

			const data = await response.json();
			setText(data.text);
		} catch (error) {
			console.error("Error:", error);
			setText("Error generating text");
		} finally {
			setLoading(false);
		}
	};

	return (
		<main style={{ padding: 32, fontFamily: "ui-sans-serif, system-ui" }}>
			<h1>Next.js + Vercel AI + Atla</h1>
			<p>Click the button to generate text. Traces will be sent to Atla.</p>

			<button
				type="button"
				onClick={generateText}
				disabled={loading}
				style={{
					padding: "8px 16px",
					backgroundColor: loading ? "#ccc" : "#007acc",
					color: "white",
					border: "none",
					borderRadius: "4px",
					cursor: loading ? "not-allowed" : "pointer",
				}}
			>
				{loading ? "Generating..." : "Generate Haiku"}
			</button>

			{text && (
				<div
					style={{
						marginTop: 20,
						padding: 16,
						backgroundColor: "#f5f5f5",
						borderRadius: "4px",
						whiteSpace: "pre-wrap",
					}}
				>
					<strong>Generated Text:</strong>
					<br />
					{text}
				</div>
			)}
		</main>
	);
}
