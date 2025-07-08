#!/usr/bin/env python3
# Tests for server configuration in the cBioPortal MCP Server

import pytest

from cbioportal_server import CBioPortalMCPServer
from config import Configuration


@pytest.mark.asyncio
async def test_api_url_configuration():
    """Test that the API URL is configured correctly."""
    # Default URL
    config_default = Configuration()
    server_default = CBioPortalMCPServer(config=config_default)
    assert server_default.base_url == "https://www.cbioportal.org/api"

    # Custom URL  
    config_custom = Configuration()
    custom_url = "https://custom-cbioportal.example.org/api"
    config_custom._config['server']['base_url'] = custom_url
    server_custom = CBioPortalMCPServer(config=config_custom)
    assert server_custom.base_url == custom_url
