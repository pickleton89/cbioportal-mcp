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


def test_configuration_falsy_values():
    """Test that Configuration.get() correctly handles falsy values like 0, False, empty strings."""
    config = Configuration()
    
    # Test with 0 (should return 0, not default)
    config._config['test'] = {'port': 0}
    assert config.get('test.port', 8080) == 0
    
    # Test with False (should return False, not default)
    config._config['test']['enabled'] = False
    assert config.get('test.enabled', True) is False
    
    # Test with empty string (should return empty string, not default)
    config._config['test']['name'] = ""
    assert config.get('test.name', 'default') == ""
    
    # Test with None (should return default)
    config._config['test']['value'] = None
    assert config.get('test.value', 'default') == 'default'
    
    # Test with missing key (should return default)
    assert config.get('test.missing', 'default') == 'default'
