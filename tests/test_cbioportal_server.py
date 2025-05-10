#!/usr/bin/env python3
# Tests for basic functionality of the cBioPortal MCP Server

import sys
import os
import pytest
from unittest.mock import patch, AsyncMock, call
import httpx

# Add the parent directory to the path so we can import the cbioportal_server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cbioportal_server import CBioPortalMCPServer

# Pytest Fixtures
@pytest.fixture
def mock_study_data():
    """Mock data for a single study."""
    return {
        "studyId": "study_1",
        "name": "Test Study",
        "description": "A study for testing",
        "publicStudy": True,
        "cancerTypeId": "mixed"
    }

@pytest.fixture
def mock_gene_data():
    """Mock data for a single gene."""
    return {
        "entrezGeneId": 672,
        "hugoGeneSymbol": "BRCA1",
        "type": "protein-coding"
    }

@pytest.fixture
def cbioportal_server_instance():
    """Fixture for CBioPortalMCPServer instance with default URL."""
    return CBioPortalMCPServer(base_url="https://www.cbioportal.org/api")

# New Fixtures for get_multiple_studies
@pytest.fixture
def mock_study_detail_brca():
    return {"studyId": "brca_tcga", "name": "BRCA TCGA", "description": "Breast Cancer TCGA"}

@pytest.fixture
def mock_study_detail_luad():
    return {"studyId": "luad_tcga", "name": "LUAD TCGA", "description": "Lung Adenocarcinoma TCGA"}

# New Fixtures for get_multiple_genes
@pytest.fixture
def mock_gene_detail_tp53():
    return {"entrezGeneId": 7157, "hugoGeneSymbol": "TP53", "type": "protein-coding"}

@pytest.fixture
def mock_gene_detail_brca1():
    return {"entrezGeneId": 672, "hugoGeneSymbol": "BRCA1", "type": "protein-coding"}

@pytest.fixture
def mock_gene_batch_response_page1(): 
    return [
        {"entrezGeneId": 7157, "hugoGeneSymbol": "TP53", "type": "protein-coding"},
        {"entrezGeneId": 672, "hugoGeneSymbol": "BRCA1", "type": "protein-coding"}
    ]

# Test Functions

@patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
@pytest.mark.asyncio
async def test_get_study_details(mock_api_request, cbioportal_server_instance, mock_study_data):
    """Test that study details retrieval works correctly."""
    study_id = "study_1"
    mock_api_request.return_value = mock_study_data
    
    result = await cbioportal_server_instance.get_study_details(study_id)
    
    mock_api_request.assert_called_once_with("studies/" + study_id)
    assert result["study"] == mock_study_data

@patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
@pytest.mark.asyncio
async def test_get_genes(mock_api_request, cbioportal_server_instance, mock_gene_data):
    """Test gene retrieval works correctly."""
    gene_ids_input = ["BRCA1", "672"]
    mock_api_request.return_value = [mock_gene_data]
    
    result = await cbioportal_server_instance.get_genes(
        gene_ids=gene_ids_input,
        gene_id_type="HUGO_GENE_SYMBOL",
        projection="SUMMARY"
    )
    
    mock_api_request.assert_called_once_with(
        "genes/fetch", 
        method="POST",
        params={
            "geneIdType": "HUGO_GENE_SYMBOL",
            "projection": "SUMMARY"
        },
        json_data=gene_ids_input
    )
    
    assert result["genes"] == [mock_gene_data]

@pytest.mark.parametrize(
    "method_name_to_test, method_args, method_kwargs, exception_to_raise, expected_error_prefix",
    [
        (
            "get_study_details",
            ("non_existent_study",), # args tuple
            {}, # kwargs dict
            httpx.HTTPStatusError(
                message="404 Client Error: Not Found for url: /api/studies/non_existent_study",
                request=httpx.Request("GET", "/api/studies/non_existent_study"),
                response=httpx.Response(404, request=httpx.Request("GET", "/api/studies/non_existent_study"))
            ),
            "Failed to get study details for non_existent_study" # Corrected prefix
        ),
        (
            "get_cancer_studies",
            (), # args tuple
            {"page_number": 0, "page_size": 10}, # kwargs dict
            httpx.RequestError(
                message="Timeout occurred while requesting /api/studies",
                request=httpx.Request("GET", "/api/studies")
            ),
            "Failed to get cancer studies"
        ),
        (
            "get_molecular_profiles",
            ("study_123",), # args: study_id
            {"page_number": 0, "page_size": 10}, # kwargs
            httpx.HTTPStatusError(
                message="500 Server Error: Internal Server Error for url: /api/studies/study_123/molecular-profiles",
                request=httpx.Request("GET", "/api/studies/study_123/molecular-profiles"),
                response=httpx.Response(500, request=httpx.Request("GET", "/api/studies/study_123/molecular-profiles"))
            ),
            "Failed to get molecular profiles for study_123"
        ),
        (
            "get_genes", # Corrected method name to use the batch/multiple gene fetcher
            (["TP53"],), # args: gene_ids as a list
            {"gene_id_type": "HUGO_SYMBOL", "projection": "SUMMARY"}, # kwargs
            httpx.RequestError(
                message="Network error while fetching gene TP53",
                request=httpx.Request("GET", "/api/genes/fetch") # Endpoint for get_genes is /genes/fetch (POST)
            ),
            "Failed to get gene information" # Corrected prefix based on get_genes implementation
        ),
        # New test cases for get_clinical_data
        (
            "get_clinical_data",
            ("study_forbidden",), # args: study_id
            {}, # kwargs: no attribute_ids, fetch all
            httpx.HTTPStatusError(
                message="403 Client Error: Forbidden for url: /api/studies/study_forbidden/clinical-data",
                request=httpx.Request("GET", "/api/studies/study_forbidden/clinical-data"),
                response=httpx.Response(403, request=httpx.Request("GET", "/api/studies/study_forbidden/clinical-data"))
            ),
            "Failed to get clinical data for study study_forbidden"
        ),
        (
            "get_clinical_data",
            ("study_network_error",), # args: study_id
            {"attribute_ids": ["ATTR1", "ATTR2"]}, # kwargs: specific attributes
            httpx.RequestError(
                message="Network error while fetching clinical data for study_network_error",
                request=httpx.Request("POST", "/api/studies/study_network_error/clinical-data/fetch") # POST for specific attributes
            ),
            "Failed to get clinical data for study study_network_error"
        ),
        # Add test cases for other critical methods like:
        # - get_all_clinical_attributes_in_study (can be covered by get_clinical_data with no attribute_ids)
        # - get_clinical_data_for_case (need to verify if a direct method exists or how to test this scenario)
        # - etc., with various 4xx/5xx errors and RequestErrors
    ]
)
@patch("cbioportal_server.CBioPortalMCPServer._make_api_request")
@pytest.mark.asyncio
async def test_generic_api_error_handling(
    mock_make_api_request, # Renamed from mock_api_request for clarity if it was different
    cbioportal_server_instance,
    method_name_to_test,
    method_args,
    method_kwargs,
    exception_to_raise,
    expected_error_prefix
):
    """Test generic error handling for API calls that raise httpx exceptions."""
    server = cbioportal_server_instance
    mock_make_api_request.side_effect = exception_to_raise

    method_to_call = getattr(server, method_name_to_test)

    # For get_genes, the first argument is gene_ids (a list)
    # The method_args tuple from parametrize will be like ( (["TP53"],) , )
    # We need to ensure it's called as method_to_call( ["TP53"], **kwargs ) not method_to_call( ("TP53",), **kwargs)
    # This is a bit tricky with getattr and *args. Let's handle it based on method name for now.
    
    actual_args = []
    if method_name_to_test == "get_genes" and len(method_args) == 1 and isinstance(method_args[0], tuple):
        actual_args = list(method_args[0]) # Unpack the inner tuple for get_genes's gene_ids list
    else:
        actual_args = list(method_args)

    result = await method_to_call(*actual_args, **method_kwargs)

    assert "error" in result, f"Result should contain an error key for {method_name_to_test}"
    assert expected_error_prefix in result["error"], \
        f"Error message for {method_name_to_test} did not contain expected prefix '{expected_error_prefix}'. Got: {result['error']}"
    
    # Ensure the original exception's message is part of the returned error string
    assert str(exception_to_raise.args[0] if exception_to_raise.args else str(exception_to_raise)) in result["error"], \
        f"Error message for {method_name_to_test} did not contain the original exception message. Got: {result['error']}"

    # Verify _make_api_request was called (or attempted)
    # Specific call arguments for _make_api_request depend on the wrapper method, 
    # so just checking it was called is a good first step.
    assert mock_make_api_request.called, f"_make_api_request was not called for {method_name_to_test}"

def test_api_url_configuration():
    """Test that the API URL is configured correctly."""
    # Default URL
    server_default = CBioPortalMCPServer()
    assert server_default.base_url == "https://www.cbioportal.org/api"
    
    # Custom URL
    custom_url = "https://custom-cbioportal.example.org/api"
    server_custom = CBioPortalMCPServer(base_url=custom_url)
    assert server_custom.base_url == custom_url

def test_lifecycle_hooks_registered(cbioportal_server_instance):
    """Test that startup and shutdown hooks are correctly registered with FastMCP."""
    server = cbioportal_server_instance
    assert server.mcp.on_startup == [server.startup]
    assert server.mcp.on_shutdown == [server.shutdown]

@pytest.mark.asyncio
async def test_startup_initializes_client(cbioportal_server_instance):
    """Test that the startup method initializes the httpx.AsyncClient."""
    server = cbioportal_server_instance
    assert server.client is None  # Check initial state before startup

    await server.startup()

    assert isinstance(server.client, httpx.AsyncClient)
    assert not server.client.is_closed
    
    # Cleanup: ensure client is closed after test
    await server.shutdown()

@pytest.mark.asyncio
async def test_shutdown_closes_client(cbioportal_server_instance):
    """Test that the shutdown method closes the httpx.AsyncClient."""
    server = cbioportal_server_instance
    
    # First, run startup to initialize the client
    await server.startup()
    assert server.client is not None, "Client should be initialized by startup"
    
    # Mock the aclose method of the actual client instance
    # This ensures we are testing the shutdown behavior on an active client
    client_to_close = server.client
    client_to_close.aclose = AsyncMock() 

    await server.shutdown()
    
    client_to_close.aclose.assert_called_once()
    # Note: server.client itself is not set to None by the current shutdown(), which is acceptable.
    # The main thing is that aclose() was called on the active client.

@pytest.mark.asyncio
async def test_tool_registration(cbioportal_server_instance):
    """Test that all intended public methods are registered as MCP tools and others are not."""
    server = cbioportal_server_instance
    
    # Fetch the list of tool names from FastMCP's public API
    registered_mcp_tools = await server.mcp.get_tools()
    registered_tool_names = set(registered_mcp_tools) # Corrected: get_tools() returns tool names (strings)

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
    }

    # Check that all expected tools are registered
    assert expected_tools.issubset(registered_tool_names), \
        f"Missing tools: {expected_tools - registered_tool_names}"

    # Check that no unexpected tools (like private or lifecycle methods) are registered
    # The _register_tools method already has an exclusion list. 
    # We can verify its effectiveness by checking against a few key exclusions.
    excluded_methods = {
        "startup", 
        "shutdown", 
        "_make_api_request", 
        "_register_tools",
        "client", # attribute
        "mcp",    # attribute
        "base_url"# attribute
    }
    
    unexpectedly_registered = excluded_methods.intersection(registered_tool_names)
    assert not unexpectedly_registered, \
        f"Unexpectedly registered tools: {unexpectedly_registered}"

    # Optional: Check if the number of registered tools exactly matches the expected count
    # This helps catch if new methods were added to the class but not to the expected_tools list or vice-versa.
    assert len(registered_tool_names) == len(expected_tools), \
        f"Mismatch in tool count. Expected {len(expected_tools)}, got {len(registered_tool_names)}. \
        Registered: {registered_tool_names}. Expected: {expected_tools}"

# --- Tests for get_multiple_studies ---
@pytest.mark.asyncio
@patch("cbioportal_server.CBioPortalMCPServer._make_api_request")
async def test_get_multiple_studies_success(
    mock_make_api_request,
    cbioportal_server_instance,
    mock_study_detail_brca,
    mock_study_detail_luad
):
    server = cbioportal_server_instance
    study_ids_to_fetch = ["brca_tcga", "luad_tcga"]

    # Configure mock_make_api_request to return different details for different study IDs
    async def side_effect_func(url, *args, **kwargs):
        if "studies/brca_tcga" in url:
            return mock_study_detail_brca
        elif "studies/luad_tcga" in url:
            return mock_study_detail_luad
        raise ValueError(f"Unexpected URL for _make_api_request: {url}")

    mock_make_api_request.side_effect = side_effect_func

    result = await server.get_multiple_studies(study_ids=study_ids_to_fetch)

    assert len(result["studies"]) == 2
    assert result["studies"]["brca_tcga"] == mock_study_detail_brca
    assert result["studies"]["luad_tcga"] == mock_study_detail_luad
    assert result["metadata"]["count"] == 2
    assert result["metadata"]["errors"] == 0
    assert result["metadata"]["concurrent"] is True

    # Check that _make_api_request was called for each study
    expected_calls = [
        call("studies/brca_tcga"),
        call("studies/luad_tcga"),
    ]
    # Note: The order of calls from asyncio.gather is not guaranteed.
    # So we check that all expected calls were made, regardless of order.
    mock_make_api_request.assert_has_calls(expected_calls, any_order=True)
    assert mock_make_api_request.call_count == 2

@pytest.mark.asyncio
@patch("cbioportal_server.CBioPortalMCPServer._make_api_request")
async def test_get_multiple_studies_partial_failure(
    mock_make_api_request,
    cbioportal_server_instance,
    mock_study_detail_brca
):
    server = cbioportal_server_instance
    study_ids_to_fetch = ["brca_tcga", "failed_study", "another_failed_study"]

    # Configure mock_make_api_request
    async def side_effect_func(url, *args, **kwargs):
        if "studies/brca_tcga" in url:
            return mock_study_detail_brca # Success
        elif "studies/failed_study" in url:
            raise Exception("Simulated API error for failed_study") # Failure 1
        elif "studies/another_failed_study" in url:
            # Simulate another way an error might be caught by the inner try-except
            # For example, if _make_api_request itself returned an error structure recognized by fetch_study
            # However, the current fetch_study catches generic Exception from _make_api_request call
            raise ValueError("Simulated internal error for another_failed_study") # Failure 2
        raise ValueError(f"Unexpected URL for _make_api_request: {url}")

    mock_make_api_request.side_effect = side_effect_func

    result = await server.get_multiple_studies(study_ids=study_ids_to_fetch)

    assert len(result["studies"]) == 3
    assert result["studies"]["brca_tcga"] == mock_study_detail_brca
    assert "error" in result["studies"]["failed_study"]
    assert result["studies"]["failed_study"]["error"] == "Simulated API error for failed_study"
    assert "error" in result["studies"]["another_failed_study"]
    assert result["studies"]["another_failed_study"]["error"] == "Simulated internal error for another_failed_study"

    assert result["metadata"]["count"] == 3
    assert result["metadata"]["errors"] == 2 # Two errors expected
    assert result["metadata"]["concurrent"] is True

    expected_calls = [
        call("studies/brca_tcga"),
        call("studies/failed_study"),
        call("studies/another_failed_study"),
    ]
    mock_make_api_request.assert_has_calls(expected_calls, any_order=True)
    assert mock_make_api_request.call_count == 3

@pytest.mark.asyncio
@patch("cbioportal_server.CBioPortalMCPServer._make_api_request")
async def test_get_multiple_studies_empty_list(
    mock_make_api_request,
    cbioportal_server_instance
):
    server = cbioportal_server_instance
    study_ids_to_fetch = []

    result = await server.get_multiple_studies(study_ids=study_ids_to_fetch)

    assert len(result["studies"]) == 0
    assert result["metadata"]["count"] == 0
    assert result["metadata"]["errors"] == 0
    # 'concurrent' might not be meaningful here, but the method sets it based on its nature
    # assert result["metadata"]["concurrent"] is True # Or check if it's absent/False for empty

    mock_make_api_request.assert_not_called()

# --- Tests for get_multiple_genes ---
@pytest.mark.asyncio
@patch("cbioportal_server.CBioPortalMCPServer._make_api_request")
async def test_get_multiple_genes_single_batch_success(
    mock_make_api_request,
    cbioportal_server_instance,
    mock_gene_batch_response_page1, 
    mock_gene_detail_tp53, 
    mock_gene_detail_brca1
):
    server = cbioportal_server_instance
    gene_ids_to_fetch = ["7157", "672"] # Entrez IDs

    # Configure mock_make_api_request to return the batch response
    # The actual server method calls genes/fetch via POST with a list of IDs
    mock_make_api_request.return_value = mock_gene_batch_response_page1

    result = await server.get_multiple_genes(gene_ids=gene_ids_to_fetch, gene_id_type="ENTREZ_GENE_ID")

    assert len(result["genes"]) == 2
    # The server method keys the results by stringified gene ID
    assert result["genes"]["7157"] == mock_gene_detail_tp53
    assert result["genes"]["672"] == mock_gene_detail_brca1
    assert result["metadata"]["count"] == 2
    assert result["metadata"]["total_requested"] == 2
    assert result["metadata"]["errors"] == 0
    assert result["metadata"]["concurrent"] is True
    assert result["metadata"]["batches"] == 1 # Single batch for this small list

    # Check that _make_api_request was called correctly for the batch
    mock_make_api_request.assert_called_once_with(
        "genes/fetch",
        method="POST",
        params={"geneIdType": "ENTREZ_GENE_ID", "projection": "SUMMARY"},
        json_data=gene_ids_to_fetch # The server method sends the list of IDs as JSON data
    )

@pytest.mark.asyncio
@patch("cbioportal_server.CBioPortalMCPServer._make_api_request")
async def test_get_multiple_genes_multiple_batches_success(
    mock_make_api_request,
    cbioportal_server_instance,
    mock_gene_detail_tp53, 
    mock_gene_detail_brca1
):
    server = cbioportal_server_instance
    # Create a list of 150 unique gene IDs (strings)
    # Default batch_size in get_multiple_genes is 100, so this should create 2 batches.
    gene_ids_to_fetch = [str(i) for i in range(1, 151)] 

    # Simulate API responses for two batches
    # Batch 1: IDs 1-100
    mock_batch_1_response = [
        {"entrezGeneId": i, "hugoGeneSymbol": f"GENE{i}", "type": "protein-coding"} 
        for i in range(1, 101)
    ]
    # Batch 2: IDs 101-150
    mock_batch_2_response = [
        {"entrezGeneId": i, "hugoGeneSymbol": f"GENE{i}", "type": "protein-coding"} 
        for i in range(101, 151)
    ]

    # Configure mock_make_api_request side_effect for multiple calls
    async def side_effect_func(url, method, params, json_data):
        if method == "POST" and url == "genes/fetch":
            if json_data == gene_ids_to_fetch[0:100]: # First batch
                return mock_batch_1_response
            elif json_data == gene_ids_to_fetch[100:150]: # Second batch
                return mock_batch_2_response
        raise ValueError(f"Unexpected API call: {url}, {method}, {params}, {json_data}")

    mock_make_api_request.side_effect = side_effect_func

    result = await server.get_multiple_genes(gene_ids=gene_ids_to_fetch, gene_id_type="ENTREZ_GENE_ID")

    assert len(result["genes"]) == 150
    # Check a couple of genes from different batches
    assert result["genes"]["1"]["hugoGeneSymbol"] == "GENE1"
    assert result["genes"]["150"]["hugoGeneSymbol"] == "GENE150"

    assert result["metadata"]["count"] == 150
    assert result["metadata"]["total_requested"] == 150
    assert result["metadata"]["errors"] == 0
    assert result["metadata"]["concurrent"] is True
    assert result["metadata"]["batches"] == 2 # Expect two batches

    # Check that _make_api_request was called for each batch
    expected_api_calls = [
        call(
            "genes/fetch",
            method="POST",
            params={"geneIdType": "ENTREZ_GENE_ID", "projection": "SUMMARY"},
            json_data=gene_ids_to_fetch[0:100]
        ),
        call(
            "genes/fetch",
            method="POST",
            params={"geneIdType": "ENTREZ_GENE_ID", "projection": "SUMMARY"},
            json_data=gene_ids_to_fetch[100:150]
        ),
    ]
    mock_make_api_request.assert_has_calls(expected_api_calls, any_order=True)
    assert mock_make_api_request.call_count == 2

@pytest.mark.asyncio
@patch("cbioportal_server.CBioPortalMCPServer._make_api_request")
async def test_get_multiple_genes_partial_batch_failure(
    mock_make_api_request,
    cbioportal_server_instance
):
    server = cbioportal_server_instance
    # Using 150 IDs to ensure 2 batches (default batch size 100)
    gene_ids_to_fetch = [str(i) for i in range(1, 151)]

    # Simulate API response for the first batch (successful)
    mock_batch_1_response = [
        {"entrezGeneId": i, "hugoGeneSymbol": f"GENE{i}", "type": "protein-coding"} 
        for i in range(1, 101)
    ]

    # Configure mock_make_api_request: first call succeeds, second call fails
    async def side_effect_func(url, method, params, json_data):
        if json_data == gene_ids_to_fetch[0:100]: # First batch
            return mock_batch_1_response
        elif json_data == gene_ids_to_fetch[100:150]: # Second batch
            raise Exception("Simulated API error for second batch")
        raise ValueError("Unexpected API call during partial failure test")

    mock_make_api_request.side_effect = side_effect_func

    result = await server.get_multiple_genes(gene_ids=gene_ids_to_fetch, gene_id_type="ENTREZ_GENE_ID")

    # Only genes from the first successful batch should be present
    assert len(result["genes"]) == 100 
    assert result["genes"]["1"]["hugoGeneSymbol"] == "GENE1"
    assert result["genes"]["100"]["hugoGeneSymbol"] == "GENE100"
    assert "101" not in result["genes"] # Gene from failed batch should not be there

    assert result["metadata"]["count"] == 100 # Count of successfully fetched genes
    assert result["metadata"]["total_requested"] == 150
    assert result["metadata"]["errors"] == 1 # One batch failed
    assert result["metadata"]["concurrent"] is True
    assert result["metadata"]["batches"] == 2

    # Check API calls
    expected_api_calls = [
        call(
            "genes/fetch",
            method="POST",
            params={"geneIdType": "ENTREZ_GENE_ID", "projection": "SUMMARY"},
            json_data=gene_ids_to_fetch[0:100]
        ),
        call(
            "genes/fetch",
            method="POST",
            params={"geneIdType": "ENTREZ_GENE_ID", "projection": "SUMMARY"},
            json_data=gene_ids_to_fetch[100:150]
        ),
    ]
    mock_make_api_request.assert_has_calls(expected_api_calls, any_order=True)
    assert mock_make_api_request.call_count == 2

@pytest.mark.asyncio
@patch("cbioportal_server.CBioPortalMCPServer._make_api_request")
async def test_get_multiple_genes_empty_list(
    mock_make_api_request,
    cbioportal_server_instance
):
    server = cbioportal_server_instance
    gene_ids_to_fetch = []

    result = await server.get_multiple_genes(gene_ids=gene_ids_to_fetch, gene_id_type="ENTREZ_GENE_ID")

    assert len(result["genes"]) == 0
    assert result["metadata"]["count"] == 0
    assert result["metadata"]["total_requested"] == 0
    assert result["metadata"]["errors"] == 0
    assert result["metadata"]["concurrent"] is True # Method is inherently concurrent
    assert result["metadata"]["batches"] == 0

    mock_make_api_request.assert_not_called()

# More tests for get_multiple_genes will go here
