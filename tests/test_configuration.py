#!/usr/bin/env python3
# Tests for server configuration in the cBioPortal MCP Server

import sys
import os
import pytest

# Add the parent directory to the path so we can import the cbioportal_server module
# This assumes 'tests' is a subdirectory of the project root where 'cbioportal_server.py' resides.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir) # This should be the project root
sys.path.insert(0, parent_dir)

from cbioportal_server import CBioPortalMCPServer  # noqa: E402


@pytest.mark.asyncio
async def test_api_url_configuration():
    """Test that the API URL is configured correctly."""
    # Default URL
    server_default = CBioPortalMCPServer()
    assert server_default.base_url == "https://www.cbioportal.org/api"

    # Custom URL
    custom_url = "https://custom-cbioportal.example.org/api"
    server_custom = CBioPortalMCPServer(base_url=custom_url)
    assert server_custom.base_url == custom_url
