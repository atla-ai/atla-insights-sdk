import type { JestConfigWithTsJest } from "ts-jest";

const config: JestConfigWithTsJest = {
	preset: "ts-jest/presets/default-esm",
	testEnvironment: "node",
	extensionsToTreatAsEsm: [".ts"],
	transform: {
		"^.+\\.(ts|tsx)$": ["ts-jest", { useESM: true }],
	},
	moduleFileExtensions: ["ts", "tsx", "js", "jsx", "mjs", "cjs", "json"],
};

export default config;
