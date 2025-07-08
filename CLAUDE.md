# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a cBioPortal MCP (Model Context Protocol) server that provides AI assistants with access to cancer genomics data from cBioPortal. The server is built using FastMCP and implements full asynchronous support for high-performance data retrieval.

## Key Architecture

### Core Components
- **`cbioportal_server.py`** - Main MCP server implementation using FastMCP framework
- **`api_client.py`** - Dedicated HTTP client class for cBioPortal API requests
- **`tests/`** - Comprehensive test suite with 92 passing tests

### Current Refactoring State
The project is in the middle of a modular refactoring (see `REFACTOR_PLAN.md`). The APIClient has been extracted from the main server class, and all tests have been updated to work with this new structure. Future refactoring will break endpoints into separate modules.

## Development Commands

### Environment Setup
Use **uv** for package management (project now uses pyproject.toml):
```bash
# Install/sync dependencies
uv sync

# Add new dependencies
uv add package-name

# Add development dependencies
uv add --dev package-name
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_server_lifecycle.py

# Run with coverage
uv run pytest --cov=.

# Update snapshots (for snapshot testing)
uv run pytest --snapshot-update
```

### Running the Server
```bash
# Start with default settings
uv run python cbioportal_server.py

# With custom base URL
uv run python cbioportal_server.py --base-url https://custom-instance.org/api

# Or use the installed script
uv run cbioportal-mcp
```

## Testing Framework

The project uses pytest with several key plugins:
- **pytest-asyncio** - For async test support (configured in `pytest.ini`)
- **syrupy** - For snapshot testing of API responses
- **pytest-mock** - For mocking external dependencies

Test structure:
- `test_server_lifecycle.py` - Server startup/shutdown and APIClient integration
- `test_snapshot_responses.py` - API response validation using snapshots
- `test_pagination.py` - Pagination logic testing
- `test_multiple_entity_apis.py` - Bulk operations testing
- `test_error_handling.py` - Error scenarios and edge cases
- `test_input_validation.py` - Parameter validation
- `test_cli.py` - Command-line interface testing

## MCP Server Tools

The server provides these tools for AI assistants:
- `get_cancer_studies` - List available cancer studies
- `search_studies` - Search studies by keyword
- `get_study_details` - Get detailed study information
- `get_samples_in_study` - Get samples for a study
- `get_genes` - Get gene information
- `search_genes` - Search genes by keyword
- `get_mutations_in_gene` - Get mutations in a gene
- `get_clinical_data` - Get clinical data for patients
- `get_molecular_profiles` - Get molecular profiles
- `get_multiple_studies` - Concurrent study fetching
- `get_multiple_genes` - Concurrent gene retrieval

## Key Dependencies

- **mcp** (1.0.0-1.8.0) - Model Context Protocol SDK
- **fastmcp** (≥0.1.0) - High-performance MCP framework
- **httpx** (≥0.24.0) - Async HTTP client
- **pytest** ecosystem for testing (dev dependency)

All dependencies are managed through pyproject.toml and uv.lock for deterministic builds.

## Configuration

The server uses environment variables and command-line arguments for configuration. Main configuration options:
- `--base-url` - cBioPortal API base URL (default: https://www.cbioportal.org/api)
- `--transport` - Transport mechanism (currently only stdio supported)

## Performance Features

The server implements full async support with:
- Concurrent API request handling
- Bulk operations for multiple studies/genes
- 480-second timeout for long-running requests
- Performance metrics and execution timing

## Important Notes

- All API requests go through the `APIClient` class
- The server uses FastMCP for MCP protocol implementation
- Tests mock the `api_client.make_api_request` method
- Pagination is handled automatically for large result sets
- All operations are fully asynchronous for better performance