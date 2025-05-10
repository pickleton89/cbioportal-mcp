# cBioPortal MCP Server

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
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

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

### Set Up Environment

#### Option 1: Using venv and pip (standard method)

```bash
# Create a virtual environment
python -m venv cbioportal-mcp-env

# Activate the environment
# On Windows:
cbioportal-mcp-env\Scripts\activate
# On macOS/Linux:
source cbioportal-mcp-env/bin/activate
```

##### Install Dependencies with pip

```bash
# Install the MCP SDK and FastMCP framework
pip install mcp>=2.0.0

# Install additional dependencies
pip install httpx asyncio
```

#### Option 2: Using UV (faster alternative)

[UV](https://github.com/astral-sh/uv) is a modern, high-performance Python package manager and environment manager that's significantly faster than pip.

```bash
# Install UV if you don't have it yet
pipx install uv
# Or with Homebrew
# brew install uv

# Create and activate a virtual environment with UV
uv venv

# Activate the environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

##### Install Dependencies with UV

```bash
# Install the MCP SDK and FastMCP framework
uv pip install mcp>=2.0.0

# Install additional dependencies
uv pip install httpx asyncio
```

### Download the Server

Download the `cbioportal_server.py` script to your working directory or clone this repository:

```bash
git clone https://github.com/pickleton89/cbioportal-mcp.git
cd cbioportal-mcp
```

### Make the Script Executable (Linux/macOS only)

```bash
chmod +x cbioportal_server.py
```

## Usage

### Starting the Server

To start the server with default settings:

```bash
python cbioportal_server.py
```

This launches the server using the public cBioPortal API at `https://www.cbioportal.org/api`.

### Advanced Options

Customize server behavior with command-line arguments:

```bash
# Use a different cBioPortal API instance
python cbioportal_server.py --base-url https://your-cbioportal-instance.org/api

# Specify a different transport mechanism (only stdio supported currently)
python cbioportal_server.py --transport stdio
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
      "command": "python",
      "args": ["/path/to/cbioportal_server.py"],
      "env": {}
    }
  }
}
```

Replace `/path/to/cbioportal_server.py` with the actual path to your script.

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

To update to the latest version of the MCP SDK:

```bash
pip install -U mcp
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [cBioPortal](https://www.cbioportal.org/) for providing the open-access cancer genomics data platform
- [Model Context Protocol](https://github.com/model-context-protocol/mcp) for enabling AI-tool interactions
- [FastMCP](https://github.com/jlowin/fastmcp) for the high-performance MCP server framework
