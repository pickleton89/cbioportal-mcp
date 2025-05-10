#!/usr/bin/env python3
# Tests for basic functionality of the cBioPortal MCP Server

from unittest.mock import patch
import sys
import os
import pytest

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

# Test Functions

@patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
@pytest.mark.asyncio
async def test_get_study_details(mock_api_request, cbioportal_server_instance, mock_study_data):
    """Test that study details retrieval works correctly."""
    study_id = "study_1"
    mock_api_request.return_value = mock_study_data
    
    result = await cbioportal_server_instance.get_study_details(study_id)
    
    mock_api_request.assert_called_once_with(f"studies/{study_id}")
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

@patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
@pytest.mark.asyncio
async def test_error_handling(mock_api_request, cbioportal_server_instance):
    """Test error handling in the API calls."""
    async def mock_side_effect(*args, **kwargs):
        raise Exception("API is unavailable")
            
    mock_api_request.side_effect = mock_side_effect
    
    result = await cbioportal_server_instance.get_cancer_studies()
    
    assert "error" in result
    assert "Failed to get cancer studies" in result["error"]
    assert "API is unavailable" in result["error"]

def test_api_url_configuration():
    """Test that the API URL is configured correctly."""
    # Default URL
    server_default = CBioPortalMCPServer()
    assert server_default.base_url == "https://www.cbioportal.org/api"
    
    # Custom URL
    custom_url = "https://custom-cbioportal.example.org/api"
    server_custom = CBioPortalMCPServer(base_url=custom_url)
    assert server_custom.base_url == custom_url
