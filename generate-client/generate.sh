#!/bin/bash

# OpenAPI Client Generation Script
# Generates a Python client from the OpenAPI schema

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENAPI_URL="https://app.atla-ai.com/api/openapi"
OUTPUT_DIR="$PROJECT_ROOT/src/atla_insights/client"
CONFIG_FILE="$SCRIPT_DIR/config.json"

echo "🔧 Generating Atla Insights OpenAPI Client"
echo "=========================================="
echo "Script dir: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo "Output dir: $OUTPUT_DIR"
echo "Config file: $CONFIG_FILE"
echo ""

# Check if openapi-generator is available
if ! command -v openapi-generator &> /dev/null; then
    echo "❌ Error: openapi-generator is not installed or not in PATH"
    echo "Please install it first:"
    echo "  brew install openapi-generator"
    echo "  or visit: https://openapi-generator.tech/docs/installation"
    exit 1
fi

# Check if the API is running (optional - we'll download the schema)
echo "📡 Downloading OpenAPI schema..."
if ! curl -s -f "$OPENAPI_URL" > "$SCRIPT_DIR/openapi.json"; then
    echo "⚠️  Warning: Could not download schema from $OPENAPI_URL"
    echo "Make sure the production API is accessible at app.atla-ai.com"
    echo ""
    
    # Check if we have a cached version
    if [ -f "$SCRIPT_DIR/openapi.json" ]; then
        echo "📂 Using cached schema from previous run"
    else
        echo "❌ No schema available. Please start your API server and try again."
        exit 1
    fi
else
    echo "✅ Schema downloaded successfully"
fi

# Remove only the generated client directory, preserving custom wrapper files
if [ -d "$OUTPUT_DIR/_generated_client" ]; then
    echo "🗑️  Removing existing generated client..."
    rm -rf "$OUTPUT_DIR/_generated_client"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Copy ignore file to output directory
echo "📋 Setting up .openapi-generator-ignore..."
cp "$SCRIPT_DIR/.openapi-generator-ignore" "$OUTPUT_DIR/.openapi-generator-ignore"

# Generate the client
echo "⚙️  Generating client with openapi-generator..."
openapi-generator generate \
    -i "$SCRIPT_DIR/openapi.json" \
    -g python \
    -o "$OUTPUT_DIR" \
    -c "$CONFIG_FILE" \
    --openapi-normalizer FILTER="tag:SDK" \
    --skip-validate-spec

# Check if generation was successful
if [ $? -eq 0 ]; then
    # Fix generated imports to use full module paths
    echo "🔧 Fixing generated imports..."
    find "$OUTPUT_DIR/_generated_client" -name "*.py" -type f -exec sed -i '' 's/^from _generated_client\./from atla_insights.client._generated_client./g' {} +
    find "$OUTPUT_DIR/_generated_client" -name "*.py" -type f -exec sed -i '' 's/^import _generated_client\./import atla_insights.client._generated_client./g' {} +
    find "$OUTPUT_DIR/_generated_client" -name "*.py" -type f -exec sed -i '' 's/^from _generated_client import/from atla_insights.client._generated_client import/g' {} +
    find "$OUTPUT_DIR/_generated_client" -name "*.py" -type f -exec sed -i '' 's/getattr(_generated_client\.models/getattr(atla_insights.client._generated_client.models/g' {} +
    echo "✅ Import fixes applied"
    
    echo ""
    echo "✅ Client generation completed successfully!"
    echo ""
    echo "📁 Generated files in: $OUTPUT_DIR"
    echo "📄 Package name: _generated_client"
    echo ""
    echo "Next steps:"
    echo "  1. Review the generated client in: $OUTPUT_DIR"
    echo "  2. Check the documentation in: $OUTPUT_DIR/docs/"
    echo "  3. Test the client with your API"
    echo ""
else
    echo "❌ Client generation failed!"
    exit 1
fi