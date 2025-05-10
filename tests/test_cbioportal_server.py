#!/usr/bin/env python3
# Tests for basic functionality of the cBioPortal MCP Server

import sys
import os
import pytest
import httpx
from unittest.mock import AsyncMock

# Add the parent directory to the path so we can import the cbioportal_server module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from cbioportal_server import CBioPortalMCPServer # noqa: E402, F401


@pytest.mark.asyncio
async def test_server_lifecycle_hooks_registered(cbioportal_server_instance_unstarted):
    """Test that startup and shutdown hooks are correctly registered on the MCP instance."""
    server = cbioportal_server_instance_unstarted
    assert server.mcp.on_startup == [server.startup], \
        "Startup hook not correctly registered"
    assert server.mcp.on_shutdown == [server.shutdown], \
        "Shutdown hook not correctly registered"


@pytest.mark.asyncio
async def test_server_startup_initializes_client_and_logs(cbioportal_server_instance_unstarted, mocker):
    """Test server.startup() initializes AsyncClient and logs correctly."""
    server = cbioportal_server_instance_unstarted
    # Ensure client is None before startup
    server.client = None 

    mock_async_client_constructor = mocker.patch('httpx.AsyncClient', return_value=AsyncMock(spec=httpx.AsyncClient))
    mock_logger_info = mocker.patch('cbioportal_server.logger.info')

    await server.startup()

    assert server.client is not None, "Client should be initialized"
    mock_async_client_constructor.assert_called_once_with(timeout=30.0)
    assert isinstance(server.client, AsyncMock), "Client should be an instance of the mocked AsyncClient"
    mock_logger_info.assert_called_with("cBioPortal MCP Server started with async HTTP client")


@pytest.mark.asyncio
async def test_server_shutdown_closes_client_and_logs(cbioportal_server_instance_unstarted, mocker):
    """Test server.shutdown() closes the client and logs correctly if client exists."""
    server = cbioportal_server_instance_unstarted
    
    # Simulate an initialized client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    server.client = mock_client
    
    mock_logger_info = mocker.patch('cbioportal_server.logger.info')

    await server.shutdown()

    mock_client.aclose.assert_called_once()
    mock_logger_info.assert_called_with("cBioPortal MCP Server async HTTP client closed")


@pytest.mark.asyncio
async def test_server_shutdown_no_client(cbioportal_server_instance_unstarted, mocker):
    """Test server.shutdown() handles gracefully if client is None."""
    server = cbioportal_server_instance_unstarted
    server.client = None # Ensure client is None
    
    mock_logger_info = mocker.patch('cbioportal_server.logger.info')

    await server.shutdown() # Should not raise an error

    # Ensure no attempt to close or log client closure if no client existed
    mock_logger_info.assert_not_called() 


@pytest.mark.asyncio
async def test_register_tools_adds_public_methods(cbioportal_server_instance_unstarted, mocker):
    """Test that _register_tools correctly adds public methods and excludes others."""
    server = cbioportal_server_instance_unstarted
    # _register_tools is called in __init__, so tools should already be registered.
    
    # Mock logger.debug to prevent console output during test if _register_tools logs
    mocker.patch('cbioportal_server.logger.debug')

    registered_tools = await server.mcp.get_tools()

    # Spot check a few expected public methods
    expected_tool_names = [
        "get_cancer_studies",
        "get_cancer_types",
        "get_genes",
        "get_multiple_studies",
        "get_multiple_genes",
        "paginate_results",      # Currently expected to be registered
        "collect_all_results"    # Currently expected to be registered
    ]
    for tool_name in expected_tool_names:
        assert tool_name in registered_tools, f"Expected tool '{tool_name}' not registered"
        assert registered_tools[tool_name].fn == getattr(server, tool_name), \
            f"Registered tool '{tool_name}' is not the correct method object"

    # Spot check a few methods/attributes that should NOT be registered
    excluded_names = [
        "_make_api_request",
        "_register_tools",
        "startup",
        "shutdown",
        "mcp", 
        "client",
        "base_url",
        "__init__"
    ]
    for excluded_name in excluded_names:
        assert excluded_name not in registered_tools, \
            f"Excluded/private method '{excluded_name}' was incorrectly registered"
