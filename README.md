# cBioPortal MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-compatible-blue.svg)](https://github.com/astral-sh/uv)
[![MCP](https://img.shields.io/badge/MCP-2.0+-green.svg)](https://github.com/model-context-protocol/mcp)
[![FastMCP](https://img.shields.io/badge/FastMCP-compatible-orange.svg)](https://github.com/jlowin/fastmcp)

A high-performance async Model Context Protocol (MCP) server that enables AI assistants to interact with cancer genomics data from [cBioPortal](https://www.cbioportal.org/), a platform for exploring multidimensional cancer genomics datasets. Built with modern asynchronous Python for significantly faster data retrieval.

## Features

- **🔍 Cancer Studies**: Browse and search cancer studies available in cBioPortal
- **🧬 Genomic Data**: Access gene mutations, clinical data, and molecular profiles
- **🔎 Search Capabilities**: Find studies, genes, and samples with keyword search
- **📊 Multiple Data Types**: Retrieve mutations, clinical data, and study metadata
- **⚡ Async Performance**: Fully asynchronous implementation for significantly faster data retrieval (up to 4.5x faster)
- **📚 Bulk Operations**: Concurrent fetching of multiple studies and genes for enhanced performance
- **🔄 FastMCP Integration**: Built on the high-performance FastMCP framework

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

## Installation

### Prerequisites

- Python 3.10 or higher
- uv (recommended) or pip (Python package installer)
- Git (optional, for cloning the repository)

### Set Up Environment

#### Option 1: Using uv (recommended)

[uv](https://github.com/astral-sh/uv) is a modern, high-performance Python package manager and environment manager that's significantly faster than pip.

```bash
# Install uv if you don't have it yet
pipx install uv
# Or with Homebrew
# brew install uv

# Clone the repository
git clone https://github.com/pickleton89/cbioportal-mcp.git
cd cbioportal-mcp

# uv automatically creates a virtual environment and installs dependencies
uv sync
```

#### Option 2: Using pip (traditional method)

```bash
# Create a virtual environment
python -m venv cbioportal-mcp-env

# Activate the environment
# On Windows:
cbioportal-mcp-env\Scripts\activate
# On macOS/Linux:
source cbioportal-mcp-env/bin/activate

# Install dependencies
pip install mcp>=1.0.0,<=1.8.0 httpx>=0.24.0 fastmcp>=0.1.0
```

### Make the Script Executable (Linux/macOS only)

If using pip installation:
```bash
chmod +x cbioportal_server.py
```

## Usage

### Starting the Server

#### With uv (recommended)

```bash
# Start the server with default settings
uv run python cbioportal_server.py

# Or use the installed script
uv run cbioportal-mcp
```

#### With traditional Python

```bash
# Start the server with default settings
python cbioportal_server.py
```

This launches the server using the public cBioPortal API at `https://www.cbioportal.org/api`.

### Advanced Options

Customize server behavior with command-line arguments:

```bash
# Using uv
uv run python cbioportal_server.py --base-url https://your-cbioportal-instance.org/api

# Using traditional Python
python cbioportal_server.py --base-url https://your-cbioportal-instance.org/api

# Specify a different transport mechanism (only stdio supported currently)
uv run python cbioportal_server.py --transport stdio
```

## Configuration

### Using with Claude Desktop

1. Install Claude Desktop
2. Open Claude Desktop
3. Click on the MCP Servers icon in the toolbar
4. Add a new MCP server with the following configuration:

```json
{
  "mcpServers": {
    "cbioportal": {
      "command": "/Users/jeffkiefer/Documents/projects/cbioportal_MCP/.venv/bin/python3",
      "args": ["/Users/jeffkiefer/Documents/projects/cbioportal_MCP/cbioportal_server.py"],
      "env": {}
    }
  }
}
```

**Note:** Make sure to replace the paths with the actual paths to your Python executable and server script. The `command` field should point to the Python executable in your virtual environment (e.g., `.venv/bin/python3`), and the first element of the `args` array should be the path to the `cbioportal_server.py` script. If you encounter an `ENOTDIR` error, ensure that the `command` field is correctly set to the Python executable and not a directory.

### Using with VS Code

Configure the MCP server in your workspace settings:

```json
{
  "mcp.servers": {
    "cbioportal": {
      "command": "python",
      "args": ["/path/to/cbioportal_server.py"]
    }
  }
}
```

## Available Tools

The cBioPortal MCP server provides the following tools:

| Tool Name | Description |
|-----------|-------------|
| `get_cancer_studies` | List all available cancer studies in cBioPortal |
| `get_cancer_types` | Get a list of all cancer types |
| `get_study_details` | Get detailed information about a specific cancer study |
| `get_samples_in_study` | Get a list of samples associated with a study |
| `get_genes` | Get information about specific genes by their Hugo symbol or Entrez ID |
| `search_genes` | Search for genes by keyword in their symbol or name |
| `get_mutations_in_gene` | Get mutations in a specific gene for a given study |
| `get_clinical_data` | Get clinical data for patients in a study |
| `get_molecular_profiles` | Get a list of molecular profiles available for a study |
| `search_studies` | Search for cancer studies by keyword |
| `get_multiple_studies` | Fetch multiple studies concurrently for better performance |
| `get_multiple_genes` | Retrieve multiple genes concurrently with automatic batching |

## Examples

Here are examples of questions you can ask AI assistants connected to this server:

```
"What cancer studies are available in cBioPortal?"
"Search for melanoma studies in cBioPortal"
"Get information about the BRCA1 gene"
"What mutations in TP53 are present in breast cancer studies?"
"Find studies related to lung cancer"
"Get clinical data for patients in the TCGA breast cancer study"
```

## Performance

This server implements full asynchronous support for significantly improved performance when retrieving data from the cBioPortal API.

### Benchmark Results

Our testing shows significant performance improvements with the async implementation:

- **4.57x faster** for concurrent study fetching compared to sequential operations
- Efficient batched processing for retrieving multiple genes
- Consistent data quality between sequential and concurrent operations

### Bulk Operation Benefits

The server provides specialized tools for bulk operations that leverage concurrency:

- `get_multiple_studies`: Fetches multiple studies in parallel using asyncio.gather
- `get_multiple_genes`: Implements smart batching for efficient concurrent gene retrieval

These methods include detailed performance metrics, such as execution time and batch counts, to help you understand the efficiency gains.

## Troubleshooting

### Server Fails to Start

- Ensure you have Python 3.8+ installed: `python --version`
- Verify all dependencies are installed: `pip list | grep mcp`
- Check for error messages in the console

### Connection Issues with Claude Desktop

- Verify the path to the script is correct in your configuration
- Make sure the script has execute permissions
- Check the Claude logs for detailed error messages

### API Connection Issues

- Ensure you have internet connectivity
- Verify that the cBioPortal API is accessible: `curl https://www.cbioportal.org/api/cancer-types`
- Try using a different API endpoint if available

## Development

### Extending the Server

You can extend the functionality of the server by adding new methods to the `CBioPortalMCPServer` class and registering them as tools:

```python
# Add a new method
def my_new_tool(self, parameter1: str, parameter2: int) -> Dict:
    # Implementation
    return {"result": "data"}

# Register the new tool
self.mcp.tool()(self.my_new_tool)
```

### Future Improvements

Potential improvements for future versions:

- Caching for frequently accessed data
- Authentication support for private cBioPortal instances
- Additional endpoints for more comprehensive data access
- Fine-tuning concurrency limits based on server capabilities
- Add request retry mechanisms for more robust error handling
- Implement more concurrent bulk operation methods for other endpoints

### Updates and Maintenance

To update dependencies:

#### With uv (recommended)
```bash
uv sync --upgrade
```

#### With pip
```bash
pip install -U mcp
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [cBioPortal](https://www.cbioportal.org/) for providing the open-access cancer genomics data platform
- [Model Context Protocol](https://github.com/model-context-protocol/mcp) for enabling AI-tool interactions
- [FastMCP](https://github.com/jlowin/fastmcp) for the high-performance MCP server framework
