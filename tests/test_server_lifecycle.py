#!/usr/bin/env python3
# Tests for server lifecycle management and tool registration

import pytest
import httpx
from unittest.mock import AsyncMock

# CBioPortalMCPServer import removed as it's not directly used by name in this file.
# Fixtures from conftest.py provide instances of CBioPortalMCPServer.


@pytest.mark.asyncio
async def test_lifecycle_hooks_registered(cbioportal_server_instance):
    """Test that startup and shutdown hooks are correctly registered with FastMCP."""
    server = cbioportal_server_instance
    assert server.startup in server.mcp.on_startup
    assert server.shutdown in server.mcp.on_shutdown


@pytest.mark.asyncio
async def test_tool_registration(cbioportal_server_instance):
    """Test that all intended public methods are registered as MCP tools and others are not."""
    server = cbioportal_server_instance
    registered_tools = await server.mcp.get_tools()
    registered_tool_names = set(registered_tools)

    # Expected public API methods that should be registered (corrected list)
    expected_tools = {
        "paginate_results",
        "collect_all_results",
        "get_cancer_studies",
        "get_cancer_types",
        "get_samples_in_study",
        "search_genes",
        "search_studies",
        "get_molecular_profiles",
        "get_mutations_in_gene",
        "get_clinical_data",
        "get_study_details",
        "get_multiple_studies",
        "get_multiple_genes",
        "get_genes",
        "get_sample_list_id",
        "get_gene_panels_for_study",
        "get_gene_panel_details",
    }

    # Methods that should NOT be registered (internal, lifecycle, etc.) (corrected list)
    non_expected_tools = {
        "startup",
        "shutdown",
        "_make_api_request",
        "_register_tools",
        "_paginate_results", # _paginate_results is an internal helper, paginate_results (public) is expected
        "__init__",
        "_fetch_study_details_concurrently",
        "_fetch_gene_details_concurrently_batched",
        "client",  # attribute
        "mcp",  # attribute
        "base_url",  # attribute
    }

    # Check that all expected tools are registered
    assert expected_tools.issubset(registered_tool_names), \
        f"Missing tools: {expected_tools - registered_tool_names}"

    # Check that no non-expected tools are registered
    unexpectedly_registered = non_expected_tools.intersection(registered_tool_names)
    # Filter out any tools that might appear in both expected and non-expected due to naming conventions (e.g. _paginate_results vs paginate_results)
    # The critical check is that truly internal/private methods are not exposed.
    # The _register_tools method itself should handle its exclusion list correctly.
    # Here, we primarily ensure core lifecycle and private underscored methods are not in registered_tool_names.
    assert not unexpectedly_registered, \
        f"Unexpectedly registered tools: {unexpectedly_registered}"

    # Optional: Check exact count if it's stable and known
    assert len(registered_tool_names) == len(expected_tools), \
        f"Mismatch in tool count. Expected {len(expected_tools)}, got {len(registered_tool_names)}. " \
        f"Registered: {sorted(list(registered_tool_names))}. Expected: {sorted(list(expected_tools))}"


@pytest.mark.asyncio
async def test_server_startup_initializes_async_client(
    cbioportal_server_instance_unstarted,
    mocker # Added mocker fixture
): 
    """Test that server.startup() initializes an httpx.AsyncClient and logs correctly."""
    server = cbioportal_server_instance_unstarted
    assert server.api_client._client is None, "APIClient's client should be None before startup"

    mock_api_client_logger_info = mocker.patch('api_client.logger.info')
    mock_server_logger_info = mocker.patch('cbioportal_server.logger.info')
    
    await server.startup()

    assert isinstance(server.api_client._client, httpx.AsyncClient), (
        "APIClient's client should be an httpx.AsyncClient after startup"
    )
    assert server.api_client._client.timeout.read == 30.0
    mock_api_client_logger_info.assert_any_call("APIClient's httpx.AsyncClient initialized.")
    mock_server_logger_info.assert_any_call("cBioPortal MCP Server started, APIClient initialized.")
        
    # Clean up the client created during this test
    if server.api_client and server.api_client._client:
        await server.api_client._client.aclose()
        # Set APIClient's client back to None to ensure test isolation
        server.api_client._client = None 


@pytest.mark.asyncio
async def test_server_shutdown_closes_async_client(
    cbioportal_server_instance_unstarted,
    mocker # Added mocker fixture
): 
    """Test that server.shutdown() calls aclose() on the httpx.AsyncClient and logs correctly."""
    server = cbioportal_server_instance_unstarted

    # Mock the client and its aclose method
    mock_async_client = AsyncMock(spec=httpx.AsyncClient)
    # Simulate server startup having initialized the APIClient's client
    server.api_client._client = mock_async_client

    mock_api_client_logger_info = mocker.patch('api_client.logger.info')
    mock_server_logger_info = mocker.patch('cbioportal_server.logger.info')
    
    await server.shutdown()

    mock_async_client.aclose.assert_called_once()
    mock_api_client_logger_info.assert_any_call("APIClient's httpx.AsyncClient closed.")
    mock_server_logger_info.assert_any_call("cBioPortal MCP Server APIClient shut down.")
        # Ensure client is set to None after shutdown as per CBioPortalMCPServer.shutdown logic
    # This depends on actual implementation; if shutdown doesn't set to None, adjust test
    # For now, assuming it might, or that it's good practice for the test to verify client state.
    # If CBioPortalMCPServer.shutdown does `self.client = None`, this assertion is valid.
    # If not, then perhaps the fixture should ensure a clean state or this assertion is removed.
    # Based on cbioportal_server.py, it does not set self.client to None after close.
    # So, we only care that aclose was called.


@pytest.mark.asyncio
async def test_server_shutdown_handles_no_client(cbioportal_server_instance_unstarted, mocker): # Added mocker fixture
    """Test that server.shutdown() handles self.client being None gracefully and does not log closure."""
    server = cbioportal_server_instance_unstarted
    assert server.api_client._client is None  # Ensure APIClient's client is None

    mock_api_client_logger_info = mocker.patch('api_client.logger.info')
    mock_server_logger_info = mocker.patch('cbioportal_server.logger.info')

    try:
        await server.shutdown()  # Should not raise an error
    except Exception as e:
        pytest.fail(f"server.shutdown() raised an exception with no client: {e}")
    
    # The server's shutdown log is unconditional after api_client.shutdown() completes.
    # api_client.shutdown() itself won't log if its internal client was None.
    mock_api_client_logger_info.assert_any_call("APIClient's httpx.AsyncClient was already closed or not initialized.")
    mock_server_logger_info.assert_any_call("cBioPortal MCP Server APIClient shut down.")
    

@pytest.mark.asyncio
async def test_initialization(cbioportal_server_instance_unstarted):
    server = cbioportal_server_instance_unstarted
    assert server.base_url == "http://mocked.cbioportal.org/api"
    assert server.api_client._client is None  # APIClient's httpx.AsyncClient should be None initially
    assert server.mcp is not None
    registered_tools = await server.mcp.get_tools()
    # Convert tool objects to a set of names for easier assertion
    registered_tool_names = set(registered_tools)
    assert "get_cancer_studies" in registered_tool_names
