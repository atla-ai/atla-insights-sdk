# OpenAPI Client Generation

This directory contains the configuration and scripts for generating the Atla Insights Python client from the OpenAPI schema.

## Files

- `config.json` - OpenAPI generator configuration
- `generate.sh` - Client generation script  
- `README.md` - This file
- `openapi.json` - Downloaded OpenAPI schema (auto-generated)

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
2. Generate a Python client using openapi-generator
3. Output the client to `src/atla_insights/client/` directory

### Generated Output

The script generates a complete Python package:

```
src/atla_insights/client/
├── atla_insights_client/          # Main package
│   ├── api/                       # API methods
│   ├── models/                    # Pydantic models
│   ├── configuration.py           # Client configuration
│   └── ...
├── docs/                          # Auto-generated documentation
├── test/                          # Generated tests
├── requirements.txt               # Dependencies
└── setup.py                      # Package setup
```

## Configuration

The `config.json` file contains basic OpenAPI generator settings:

```json
{
  "packageName": "atla_insights_client",
  "projectName": "atla-insights-client", 
  "packageVersion": "1.0.0",
  "library": "urllib3",
  "generateSourceCodeOnly": false,
  "hideGenerationTimestamp": true
}
```

### Available Options

See all available options:
```bash
openapi-generator config-help -g python
```

Common options to consider:
- `packageName` - Python package name
- `library` - HTTP library (urllib3, asyncio)
- `generateSourceCodeOnly` - Skip setup files
- `projectName` - Project name for setup.py

## Workflow

1. **Development**: Make API changes
2. **Generate**: Run `./generate-client/generate.sh`
3. **Review**: Check generated client in `generated_client/`
4. **Test**: Use generated client with your API
5. **Iterate**: Repeat as needed

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