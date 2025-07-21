# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a cBioPortal MCP (Model Context Protocol) server that provides AI assistants with access to cancer genomics data from cBioPortal. The server is built using FastMCP and implements full asynchronous support for high-performance data retrieval.

## Key Architecture

### Core Components
- **`cbioportal_mcp/server.py`** - Main MCP server implementation using FastMCP framework
- **`cbioportal_mcp/api_client.py`** - Dedicated HTTP client class for cBioPortal API requests
- **`cbioportal_mcp/endpoints/`** - Domain-specific endpoint modules:
  - `base.py` - BaseEndpoint pattern with shared pagination, validation, and error handling
  - `studies.py` - Cancer studies endpoints
  - `genes.py` - Gene operations and mutations
  - `samples.py` - Sample data management
  - `molecular_profiles.py` - Molecular and clinical data
- **`cbioportal_mcp/utils/`** - Shared utilities for pagination, validation, and logging
- **`cbioportal_mcp/config.py`** - Multi-layer configuration system (CLI > ENV > YAML > defaults)
- **`tests/`** - Comprehensive test suite with 93 passing tests

### Architectural Patterns
- **BaseEndpoint Pattern**: All endpoint classes inherit from `BaseEndpoint`, which provides:
  - Automatic API client initialization via `_ensure_api_client_ready()`
  - Shared pagination logic with `paginated_request()`
  - Consistent error handling via `@handle_api_errors` decorator
  - Parameter validation via `@validate_paginated_params` decorator
- **Dependency Injection**: Configuration and APIClient are injected into endpoints
- **Async-First Design**: All API operations are fully asynchronous
- **Modular Structure**: Clear separation of concerns with domain-specific modules

## Development Commands

### Environment Setup
```bash
# Install/sync dependencies (using uv package manager)
uv sync

# Install in editable mode (required for Claude Desktop integration)
uv pip install -e .

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

# Run single test
uv run pytest tests/test_pagination.py::test_paginate_results_basic

# Run with coverage
uv run pytest --cov=cbioportal_mcp

# Update snapshots (for snapshot testing)
uv run pytest --snapshot-update

# Run tests matching a pattern
uv run pytest -k "test_get_multiple"
```

### Code Quality
```bash
# Run linter
uv run ruff check .

# Run linter with fixes
uv run ruff check . --fix

# Format code
uv run ruff format .

# Type checking
uv run ty .
```

### Running the Server
```bash
# Start with default settings
uv run cbioportal-mcp

# With custom configuration
uv run cbioportal-mcp --config config.yaml

# With custom base URL
uv run cbioportal-mcp --base-url https://custom-instance.org/api

# Generate example config
uv run cbioportal-mcp --create-example-config

# Debug mode
uv run cbioportal-mcp --log-level DEBUG
```

## High-Level Architecture

### Request Flow
1. AI Assistant → MCP Protocol → FastMCP → CBioPortalMCPServer
2. Server delegates to appropriate endpoint module (studies, genes, etc.)
3. Endpoint inherits from BaseEndpoint for common functionality
4. BaseEndpoint ensures API client is initialized (lazy initialization)
5. API request goes through APIClient → httpx → cBioPortal API
6. Response flows back with automatic pagination and error handling

### Configuration Hierarchy
The configuration system (`config.py`) supports multiple sources with this priority:
1. CLI arguments (highest priority)
2. Environment variables (CBIOPORTAL_*)
3. YAML configuration file
4. Default values (lowest priority)

Key environment variables:
- `CBIOPORTAL_BASE_URL` - API endpoint
- `CBIOPORTAL_LOG_LEVEL` - Logging level
- `CBIOPORTAL_CLIENT_TIMEOUT` - Request timeout
- `CBIOPORTAL_GENE_BATCH_SIZE` - Batch size for gene operations

### Error Handling Strategy
- **Validation Errors**: Raised immediately as ValueError/TypeError
- **API Errors**: Caught by `@handle_api_errors` decorator and returned as error dict
- **Network Errors**: Specific exception types (APIHTTPError, APINetworkError, etc.)
- **Lazy Initialization**: API client initialized on first use to avoid startup issues

### Performance Optimizations
- **Concurrent Operations**: `get_multiple_studies` and `get_multiple_genes` use asyncio.gather()
- **Smart Batching**: Large gene lists automatically batched (configurable size)
- **Async Generators**: Memory-efficient pagination via `paginate_results()`
- **4.5x Performance**: Concurrent vs sequential operations benchmarked

## MCP Server Tools

The server exposes these tools through FastMCP:
- `get_cancer_studies` - List available cancer studies with pagination
- `search_studies` - Search studies by keyword
- `get_study_details` - Get detailed study information
- `get_samples_in_study` - Get samples for a study
- `get_sample_list_id` - Get sample list ID for study
- `get_genes` - Get gene information by ID/symbol
- `search_genes` - Search genes by keyword
- `get_mutations_in_gene` - Get mutations in a gene
- `get_clinical_data` - Get clinical data for patients
- `get_molecular_profiles` - Get molecular profiles
- `get_gene_panels_for_study` - Get gene panels
- `get_gene_panel_details` - Get specific panel details
- `get_multiple_studies` - Concurrent study fetching
- `get_multiple_genes` - Concurrent gene retrieval

## Testing Strategy

### Test Categories
- **Lifecycle Tests** (`test_server_lifecycle.py`) - Server startup/shutdown, tool registration
- **Snapshot Tests** (`test_snapshot_responses.py`) - API response consistency
- **Pagination Tests** (`test_pagination.py`) - Pagination logic and edge cases
- **Multi-Entity Tests** (`test_multiple_entity_apis.py`) - Concurrent operations
- **Error Handling** (`test_error_handling.py`) - Network errors, API errors
- **Input Validation** (`test_input_validation.py`) - Parameter validation
- **CLI Tests** (`test_cli.py`) - Command-line interface
- **Configuration Tests** (`test_configuration.py`) - Config system validation

### Testing Best Practices
- Mock at `api_client.make_api_request` level for consistency
- Use fixtures for common test data
- Test both success and error paths
- Verify pagination metadata matches actual data
- Use snapshot testing for API response structure

## Important Implementation Details

### BaseEndpoint Pattern
All endpoint classes must:
1. Inherit from `BaseEndpoint`
2. Use `@handle_api_errors` decorator on public methods
3. Call `await self._ensure_api_client_ready()` if not using decorator
4. Use `self.paginated_request()` for paginated endpoints

### Adding New Endpoints
1. Create new file in `cbioportal_mcp/endpoints/`
2. Inherit from `BaseEndpoint`
3. Implement methods with proper decorators
4. Add endpoint instance to server initialization
5. Register methods as tools in `_register_tools()`
6. Add tests following existing patterns

### Common Pitfalls
- Forgetting `@handle_api_errors` decorator causes "APIClient._client is not initialized" errors
- Not using `paginated_request()` for endpoints that support pagination
- Modifying pagination params dict without copying first
- Not handling empty result sets in bulk operations

## Dependencies

Core dependencies (managed via pyproject.toml):
- **mcp** (1.0.0-1.8.0) - Model Context Protocol SDK
- **fastmcp** (≥0.1.0) - High-performance MCP framework
- **httpx** (≥0.24.0) - Async HTTP client
- **pyyaml** (≥6.0.2) - YAML configuration support

Development dependencies:
- **pytest** (≥7.0.0) - Testing framework
- **pytest-asyncio** (0.26.0) - Async test support
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking support
- **syrupy** - Snapshot testing
- **ruff** - Linting and formatting
- **ty** - Type checking

## Configuration Details

### Multi-Layer Configuration
```yaml
# Example config.yaml
server:
  base_url: "https://www.cbioportal.org/api"
  client_timeout: 480.0
  
logging:
  level: "INFO"
  
api:
  batch_size:
    genes: 100  # Configurable batch size
  retry:
    enabled: true
    max_attempts: 3
```

### Claude Desktop Integration
For reliable Claude Desktop integration, use direct script path:
```json
{
  "mcpServers": {
    "cbioportal": {
      "command": "/path/to/project/.venv/bin/cbioportal-mcp",
      "env": {
        "CBIOPORTAL_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Performance Characteristics

- **Startup**: Lazy API client initialization avoids connection delays
- **Concurrency**: Up to 4.5x faster for bulk operations
- **Memory**: Async generators for efficient pagination
- **Timeouts**: 480-second default for long-running requests
- **Batching**: Automatic for large gene lists (configurable)

## Code Quality Standards

- **Linting**: Ruff configuration in pyproject.toml
- **Type Hints**: Comprehensive type annotations
- **Error Messages**: Descriptive and actionable
- **Test Coverage**: Maintain high coverage (currently 93 tests)
- **Documentation**: Docstrings for all public methods