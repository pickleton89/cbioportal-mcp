# 🧬 cBioPortal MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blue.svg)](https://github.com/astral-sh/uv)
[![MCP](https://img.shields.io/badge/MCP-2.0+-green.svg)](https://github.com/model-context-protocol/mcp)
[![FastMCP](https://img.shields.io/badge/FastMCP-framework-orange.svg)](https://github.com/jlowin/fastmcp)
[![Tests](https://img.shields.io/badge/tests-92%20passing-brightgreen.svg)](#testing)
[![Code Coverage](https://img.shields.io/badge/coverage-comprehensive-brightgreen.svg)](#development)

A high-performance, production-ready **Model Context Protocol (MCP) server** that enables AI assistants to seamlessly interact with cancer genomics data from [cBioPortal](https://www.cbioportal.org/). Built with modern **async Python architecture** and **modular design** for enterprise-grade reliability and **4.5x faster performance**.

## 🌟 Overview & Key Features

### 🚀 **Performance & Architecture**
- **⚡ 4.5x Performance Boost**: Full async implementation with concurrent API operations
- **🏗️ Modular Architecture**: Professional structure with 71% code reduction (1,357 → 396 lines)
- **📦 Modern Package Management**: uv-based workflow with pyproject.toml
- **🔄 Concurrent Operations**: Bulk fetching of studies and genes with automatic batching

### 🔧 **Enterprise Features**
- **⚙️ Multi-layer Configuration**: CLI args → Environment variables → YAML config → Defaults
- **📋 Comprehensive Testing**: 92 tests across 8 organized test suites with full coverage
- **🛡️ Input Validation**: Robust parameter validation and error handling
- **📊 Pagination Support**: Efficient data retrieval with automatic pagination

### 🧬 **Cancer Genomics Capabilities**
- **🔍 Study Management**: Browse, search, and analyze cancer studies
- **🧪 Molecular Data**: Access mutations, clinical data, and molecular profiles
- **📈 Bulk Operations**: Concurrent fetching of multiple entities
- **🔎 Advanced Search**: Keyword-based discovery across studies and genes

## 🧠🤖 **AI-Collaborative Development**

This project demonstrates **cutting-edge human-AI collaboration** in bioinformatics software development:

- **🧠 Domain Expertise**: 20+ years cancer research experience guided architecture and feature requirements
- **🤖 AI Implementation**: Advanced code generation, API design, and performance optimization through systematic LLM collaboration
- **🔄 Quality Assurance**: Iterative refinement ensuring professional standards and production reliability
- **📈 Innovation Approach**: Showcases how domain experts can effectively leverage AI tools to build enterprise-grade bioinformatics platforms

**Methodology**: This collaborative approach combines deep biological domain knowledge with AI-powered development capabilities, accelerating innovation while maintaining rigorous code quality and scientific accuracy.

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** 🐍
- **uv** (modern package manager) - recommended 📦
- **Git** (optional, for cloning) 

### ⚡ Installation & Launch
```bash
# Install uv if needed
pipx install uv

# Clone and setup
git clone https://github.com/pickleton89/cbioportal-mcp.git
cd cbioportal-mcp
uv sync

# Launch server
uv run cbioportal-mcp
```

**That's it!** 🎉 Your server is running and ready for AI assistant connections.

## 📦 Installation Options

### 🔥 **Option 1: uv (Recommended)**
Modern, lightning-fast package management with automatic environment handling:

```bash
# Install uv
pipx install uv
# Or with Homebrew: brew install uv

# Clone repository
git clone https://github.com/pickleton89/cbioportal-mcp.git
cd cbioportal-mcp

# One-command setup (creates venv + installs dependencies)
uv sync

# Alternative: development mode with all dev dependencies
uv sync --group dev
```

### 🐍 **Option 2: pip (Traditional)**
Standard Python package management approach:

```bash
# Create virtual environment
python -m venv cbioportal-mcp-env

# Activate environment
# Windows: cbioportal-mcp-env\Scripts\activate
# macOS/Linux: source cbioportal-mcp-env/bin/activate

# Install dependencies
pip install -e .
```

## ⚙️ Configuration

### 🎛️ **Multi-Layer Configuration System**
The server supports flexible configuration with priority: **CLI args > Environment variables > Config file > Defaults**

#### **YAML Configuration** 📄
Create `config.yaml` for persistent settings:

```yaml
# cBioPortal MCP Server Configuration
server:
  base_url: "https://www.cbioportal.org/api"
  transport: "stdio"
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

api:
  timeout: 480
  max_retries: 3
  rate_limit: 100

# Performance settings
performance:
  concurrent_batch_size: 10
  max_concurrent_requests: 20
```

#### **Environment Variables** 🌍
```bash
export CBIOPORTAL_BASE_URL="https://custom-instance.org/api"
export CBIOPORTAL_LOG_LEVEL="DEBUG"
export CBIOPORTAL_TIMEOUT=600
```

#### **CLI Options** 💻
```bash
# Basic usage
uv run cbioportal-mcp

# Custom configuration
uv run cbioportal-mcp --config config.yaml --log-level DEBUG

# Custom API endpoint
uv run cbioportal-mcp --base-url https://custom-instance.org/api

# Generate example config
uv run cbioportal-mcp --create-example-config
```

## 🔌 Usage & Integration

### 🖥️ **Claude Desktop Integration**
Configure in your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "cbioportal": {
      "command": "uv",
      "args": ["run", "cbioportal-mcp"],
      "cwd": "/path/to/cbioportal-mcp",
      "env": {
        "CBIOPORTAL_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 🔧 **VS Code Integration**
Add to your workspace settings:

```json
{
  "mcp.servers": {
    "cbioportal": {
      "command": "uv",
      "args": ["run", "cbioportal-mcp"],
      "cwd": "/path/to/cbioportal-mcp"
    }
  }
}
```

### 🏃‍♂️ **Command Line Usage**
```bash
# Development server with debug logging
uv run python cbioportal_server.py --log-level DEBUG

# Production server with custom config
uv run cbioportal-mcp --config production.yaml

# Using custom cBioPortal instance
uv run cbioportal-mcp --base-url https://private-instance.org/api
```

## 🏗️ Architecture

### 📁 **Modern Project Structure**
```
cbioportal-mcp/
├── 📊 cbioportal_server.py      # Main MCP server (396 lines - 71% reduction!)
├── 🌐 api_client.py             # Dedicated HTTP client class
├── ⚙️ config.py                 # Multi-layer configuration system
├── 📋 constants.py              # Centralized constants
├── 📁 endpoints/                # Domain-specific API modules
│   ├── 🔬 studies.py           # Cancer studies & search
│   ├── 🧬 genes.py             # Gene operations & mutations
│   ├── 🧪 samples.py           # Sample data management
│   └── 📈 molecular_profiles.py # Molecular & clinical data
├── 📁 utils/                    # Shared utilities
│   ├── 📄 pagination.py        # Efficient pagination logic
│   ├── ✅ validation.py        # Input validation
│   └── 📝 logging.py           # Logging configuration
├── 📁 tests/                    # Comprehensive test suite (92 tests)
├── 📁 docs/                     # Documentation
├── 📁 scripts/                  # Development utilities
└── 📄 pyproject.toml           # Modern Python project config
```

### 🎯 **Design Principles**
- **🔧 Modular**: Clear separation of concerns with domain-specific modules
- **⚡ Async-First**: Full asynchronous implementation for maximum performance
- **🛡️ Robust**: Comprehensive input validation and error handling
- **🧪 Testable**: 92 tests ensuring reliability and preventing regressions
- **🔄 Maintainable**: Clean code architecture with 71% reduction in complexity

## 🛠️ Available Tools

The server provides **12 high-performance tools** for AI assistants:

| 🔧 Tool | 📝 Description | ⚡ Features |
|---------|---------------|------------|
| `get_cancer_studies` | List all available cancer studies | 📄 Pagination, 🔍 Filtering |
| `search_studies` | Search studies by keyword | 🔎 Full-text search, 📊 Sorting |
| `get_study_details` | Detailed study information | 📈 Comprehensive metadata |
| `get_samples_in_study` | Samples for specific studies | 📄 Paginated results |
| `get_genes` | Gene information by ID/symbol | 🏷️ Flexible identifiers |
| `search_genes` | Search genes by keyword | 🔍 Symbol & name search |
| `get_mutations_in_gene` | Gene mutations in studies | 🧬 Mutation details |
| `get_clinical_data` | Patient clinical information | 👥 Patient-centric data |
| `get_molecular_profiles` | Study molecular profiles | 📊 Profile metadata |
| `get_multiple_studies` | **🚀 Concurrent study fetching** | ⚡ Bulk operations |
| `get_multiple_genes` | **🚀 Concurrent gene retrieval** | 📦 Automatic batching |
| `get_gene_panels_for_study` | Gene panels in studies | 🧬 Panel information |

### 🌟 **Performance Features**
- **⚡ Concurrent Operations**: `get_multiple_*` methods use `asyncio.gather` for parallel processing
- **📦 Smart Batching**: Automatic batching for large gene lists
- **📄 Efficient Pagination**: Async generators for memory-efficient data streaming
- **⏱️ Performance Metrics**: Execution timing and batch count reporting

## 🚀 Performance

### 📊 **Benchmark Results**
Our async implementation delivers significant performance improvements:

```
🏃‍♂️ Sequential Study Fetching:  1.31 seconds (10 studies)
⚡ Concurrent Study Fetching:   0.29 seconds (10 studies)
🎯 Performance Improvement:     4.57x faster!
```

### 🔥 **Async Benefits**
- **🚀 4.5x Faster**: Concurrent API requests vs sequential operations
- **📦 Bulk Processing**: Efficient batched operations for multiple entities
- **⏱️ Non-blocking**: Asynchronous I/O prevents request blocking
- **🧮 Smart Batching**: Automatic optimization for large datasets

### 💡 **Performance Tips**
- Use `get_multiple_studies` for fetching multiple studies concurrently
- Leverage `get_multiple_genes` with automatic batching for gene lists
- Configure `concurrent_batch_size` in config for optimal performance
- Monitor execution metrics included in response metadata

## 👨‍💻 Development

### 🔨 **Development Workflow**
```bash
# Setup development environment
uv sync --group dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=.

# Run specific test file
uv run pytest tests/test_server_lifecycle.py

# Update snapshots
uv run pytest --snapshot-update

# Lint code
uv run ruff check .

# Format code  
uv run ruff format .
```

### 🧪 **Testing**
Comprehensive test suite with **92 tests** across 8 categories:

- **🔄 `test_server_lifecycle.py`** - Server startup/shutdown & tool registration
- **📄 `test_pagination.py`** - Pagination logic & edge cases
- **🚀 `test_multiple_entity_apis.py`** - Concurrent operations & bulk fetching
- **✅ `test_input_validation.py`** - Parameter validation & error handling
- **📸 `test_snapshot_responses.py`** - API response consistency (syrupy)
- **💻 `test_cli.py`** - Command-line interface & argument parsing
- **🛡️ `test_error_handling.py`** - Error scenarios & network issues
- **⚙️ `test_configuration.py`** - Configuration system validation

### 🛠️ **Development Tools**
- **📦 uv**: Modern package management (10-100x faster than pip)
- **🧪 pytest**: Testing framework with async support
- **📸 syrupy**: Snapshot testing for API responses
- **🔍 ruff**: Lightning-fast linting and formatting
- **📊 pytest-cov**: Code coverage reporting

### 🤝 **Contributing**
1. **🍴 Fork** the repository
2. **🌿 Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **✅ Test** your changes (`uv run pytest`)
4. **📝 Commit** with clear messages (`git commit -m 'Add amazing feature'`)
5. **🚀 Push** to branch (`git push origin feature/amazing-feature`)
6. **🔄 Create** a Pull Request

## 🔧 Troubleshooting

### 🚨 **Common Issues**

#### **Server Fails to Start**
```bash
# Check Python version
python --version  # Should be 3.10+

# Verify dependencies
uv sync

# Check for conflicts
uv run python -c "import mcp, httpx, fastmcp; print('Dependencies OK')"
```

#### **Claude Desktop Connection Issues**
- ✅ Verify paths in MCP configuration are absolute
- ✅ Check that `uv` is in your system PATH
- ✅ Ensure `cwd` points to project directory
- ✅ Review Claude Desktop logs for detailed errors

#### **Performance Issues**
- 🔧 Increase `concurrent_batch_size` in config
- 🔧 Adjust `max_concurrent_requests` for your system
- 🔧 Use `get_multiple_*` methods for bulk operations
- 🔧 Monitor network latency to cBioPortal API

#### **Configuration Problems**
```bash
# Generate example config
uv run cbioportal-mcp --create-example-config

# Validate configuration
uv run cbioportal-mcp --config your-config.yaml --log-level DEBUG

# Check environment variables
env | grep CBIOPORTAL
```

### 🌐 **API Connectivity**
```bash
# Test cBioPortal API accessibility
curl https://www.cbioportal.org/api/cancer-types

# Test with custom instance
curl https://your-instance.org/api/studies
```

## 💡 Examples & Use Cases

### 🔍 **Research Queries**
```
"What cancer studies are available for breast cancer research?"
"Search for melanoma studies with genomic data"
"Get mutation data for TP53 in lung cancer studies"
"Find clinical data for patients in the TCGA-BRCA study"
"What molecular profiles are available for pediatric brain tumors?"
```

### 🧬 **Genomic Analysis**
```
"Compare mutation frequencies between two cancer studies"
"Get all genes in the DNA repair pathway for ovarian cancer"
"Find studies with both RNA-seq and mutation data"
"What are the most frequently mutated genes in glioblastoma?"
```

### 📊 **Bulk Operations**
```
"Fetch data for multiple cancer studies concurrently"
"Get information for a list of cancer genes efficiently"
"Compare clinical characteristics across multiple studies"
"Retrieve molecular profiles for several cancer types"
```

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **🧬 [cBioPortal](https://www.cbioportal.org/)** - Open-access cancer genomics data platform
- **🔗 [Model Context Protocol](https://github.com/model-context-protocol/mcp)** - Enabling seamless AI-tool interactions  
- **⚡ [FastMCP](https://github.com/jlowin/fastmcp)** - High-performance MCP server framework
- **📦 [uv](https://github.com/astral-sh/uv)** - Modern Python package management
- **🤖 AI Collaboration** - Demonstrating the power of human-AI partnership in scientific software development

---

**🌟 Built with passion for cancer research and cutting-edge technology!** 🧬✨