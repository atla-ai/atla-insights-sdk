# OpenAPI Client Generation

This directory contains the configuration and scripts for generating the Atla Insights Python client from the OpenAPI schema.

## Files

- `config.json` - OpenAPI generator configuration
- `generate.sh` - Client generation script  
- `README.md` - This file
- `openapi.json` - Downloaded OpenAPI schema (auto-generated)
- `.openapi-generator-ignore` - Files to ignore during generation

## Usage

### Prerequisites

1. **OpenAPI Generator**: Install via Homebrew:
   ```bash
   brew install openapi-generator
   ```

2. **API Access**: Make sure the production API is accessible at `app.atla-ai.com`

### Generate Client

Run the generation script:

```bash
./generate-client/generate.sh
```

This will:
1. Download the OpenAPI schema from `https://app.atla-ai.com/api/openapi`
2. Generate a Python client using openapi-generator with SDK tag filtering
3. Output the client to `src/atla_insights/client/_generated_client/` directory
4. Fix imports to use proper module paths

### Generated Output

The script generates a complete Python package:

```
src/atla_insights/client/
├── _generated_client/             # Generated package
│   ├── api/                       # API methods
│   │   └── sdk_api.py            # SDK API endpoints
│   ├── models/                    # Python data models
│   ├── docs/                     # Auto-generated documentation
│   ├── test/                     # Generated tests
│   ├── configuration.py          # Client configuration
│   ├── api_client.py            # HTTP client
│   └── ...
├── client.py                     # High-level wrapper
├── types.py                      # Type definitions
└── __init__.py                   # Package exports
```

## Configuration

The `config.json` file contains basic OpenAPI generator settings:

```json
{
  "packageName": "_generated_client",
  "library": "urllib3",
  "generateSourceCodeOnly": true,
  "hideGenerationTimestamp": true,
  "datetimeFormat": "%Y-%m-%dT%H:%M:%SZ",
  "dateFormat": "%Y-%m-%d",
  "modelNameMappings": {
    "listTraces_200_response": "TraceListResponse",
    "getTracesByIds_200_response": "DetailedTraceListResponse",
    // ... additional mappings for cleaner model names
  }
}
```

### Available Options

See all available options:
```bash
openapi-generator config-help -g python
```

Key configuration options:
- `packageName` - Python package name (set to `_generated_client`)
- `library` - HTTP library (using `urllib3`)
- `generateSourceCodeOnly` - Skip setup files (set to `true`)
- `modelNameMappings` - Clean up auto-generated model names
- `datetimeFormat`/`dateFormat` - Date/time formatting in models

## Workflow

1. **Development**: Make API changes and tag endpoints with `SDK` in OpenAPI spec
2. **Generate**: Run `./generate-client/generate.sh`
3. **Review**: Check generated client in `src/atla_insights/client/_generated_client/`
4. **Update**: Modify wrapper classes in `client.py` if needed
5. **Test**: Use generated client with your API
6. **Iterate**: Repeat as needed

## Schema Caching

The script caches the downloaded OpenAPI schema as `openapi.json`. If the API server is not available, it will use the cached version.

## Troubleshooting

### Generator Not Found
```bash
brew install openapi-generator
```

### API Not Accessible
Make sure `app.atla-ai.com` is accessible, or update the `OPENAPI_URL` in the script for a different environment.

### Generation Errors
Check the openapi-generator logs and ensure your OpenAPI schema is valid.

### Import Errors
The script automatically fixes import paths. If you see import errors, ensure the generated code uses the full module path `atla_insights.client._generated_client.*`

### Missing SDK Endpoints
Ensure API endpoints are tagged with `SDK` in the OpenAPI specification. Only endpoints with this tag will be generated.