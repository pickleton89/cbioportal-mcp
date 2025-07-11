#!/usr/bin/env python3
# Tests for API endpoints that fetch single entities from cBioPortal

import pytest
from unittest.mock import patch

from cbioportal_mcp.server import CBioPortalMCPServer

# Fixtures like cbioportal_server_instance, mock_study_data, mock_gene_data
# are expected to be defined in conftest.py


@patch("cbioportal_mcp.api_client.APIClient.make_api_request")
@pytest.mark.asyncio
async def test_get_study_details(
    mock_api_request, cbioportal_server_instance: CBioPortalMCPServer, mock_study_data
):
    """Test that study details retrieval works correctly."""
    study_id = "study_1"
    mock_api_request.return_value = mock_study_data

    result = await cbioportal_server_instance.get_study_details(study_id)

    mock_api_request.assert_called_once_with("studies/" + study_id)
    assert result["study"] == mock_study_data


@patch("cbioportal_mcp.api_client.APIClient.make_api_request")
@pytest.mark.asyncio
async def test_get_genes(
    mock_api_request, cbioportal_server_instance: CBioPortalMCPServer, mock_gene_data
):
    """Test gene retrieval works correctly."""
    gene_ids_input = ["BRCA1", "672"]
    mock_api_request.return_value = [mock_gene_data]

    result = await cbioportal_server_instance.get_genes(
        gene_ids=gene_ids_input, gene_id_type="HUGO_GENE_SYMBOL", projection="SUMMARY"
    )

    mock_api_request.assert_called_once_with(
        "genes/fetch",
        method="POST",
        params={"geneIdType": "HUGO_GENE_SYMBOL", "projection": "SUMMARY"},
        json_data=gene_ids_input,
    )

    assert result["genes"] == [mock_gene_data]
