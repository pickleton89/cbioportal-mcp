# Migration to uv

This project has been migrated from pip/requirements.txt to uv's project workflow using pyproject.toml. This provides better dependency management, faster installs, and reproducible builds.

## For Existing Developers

### Quick Start
If you have an existing environment, you can start using uv immediately:

```bash
# Install uv if you don't have it
pipx install uv

# Remove old virtual environment (optional)
rm -rf .venv

# Initialize uv project and install dependencies
uv sync
```

### What Changed

1. **Dependencies**: Moved from `requirements.txt` and `requirements-dev.txt` to `pyproject.toml`
2. **Python version**: Updated minimum requirement from Python 3.8 to Python 3.10 (required by fastmcp)
3. **Package management**: Now uses `uv.lock` instead of `requirements.txt` for reproducible installs
4. **Configuration**: Moved pytest configuration from `pytest.ini` to `pyproject.toml`
5. **Entry point**: Added `cbioportal-mcp` script entry point

### Command Migration

| Old Command | New Command |
|-------------|-------------|
| `pip install -r requirements.txt` | `uv sync` |
| `pip install -r requirements-dev.txt` | `uv sync` (dev dependencies included) |
| `pip install package-name` | `uv add package-name` |
| `pip install --dev package-name` | `uv add --dev package-name` |
| `python script.py` | `uv run python script.py` |
| `pytest` | `uv run pytest` |

### Development Workflow

1. **Environment**: uv automatically manages the virtual environment in `.venv`
2. **Dependencies**: All dependencies are locked in `uv.lock` for reproducible builds
3. **Testing**: Use `uv run pytest` for testing
4. **Running**: Use `uv run python cbioportal_server.py` or `uv run cbioportal-mcp`

### Benefits of uv

- **Faster**: 10-100x faster than pip for most operations
- **Reproducible**: Universal lock file works across platforms
- **Automatic**: Automatically manages virtual environments
- **Modern**: Built-in support for PEP 621 (pyproject.toml)
- **Compatible**: Works with existing Python packages

### Troubleshooting

**Issue**: "No module named 'xyz'"
**Solution**: Run `uv sync` to ensure all dependencies are installed

**Issue**: "Python version not supported"
**Solution**: Ensure you have Python 3.10+ installed

**Issue**: "Command not found"
**Solution**: Use `uv run` prefix for commands

### Legacy Support

The old `requirements.txt` files are kept for reference but are no longer used. If you need to use pip for some reason:

```bash
# Install dependencies with pip (not recommended)
pip install mcp>=1.0.0,<=1.8.0 httpx>=0.24.0 fastmcp>=0.1.0

# Install dev dependencies
pip install pytest>=7.0.0 pytest-cov>=4.1.0 pytest-asyncio==0.26.0 pytest-mock>=3.12.0 syrupy>=4.0.0
```

For more information about uv, see the [official documentation](https://docs.astral.sh/uv/).