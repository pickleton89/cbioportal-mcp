#!/usr/bin/env python3
# Tests for API endpoints that fetch multiple entities concurrently from cBioPortal

import pytest
from unittest.mock import patch, call

from cbioportal_mcp.server import CBioPortalMCPServer

# Pytest Fixtures (e.g., cbioportal_server_instance, mock_study_detail_brca, etc.)
# are expected to be defined in conftest.py


# --- Tests for get_multiple_studies ---
@pytest.mark.asyncio
@patch("cbioportal_mcp.api_client.APIClient.make_api_request")
async def test_get_multiple_studies_success(
    mock_make_api_request,
    cbioportal_server_instance: CBioPortalMCPServer,
    mock_study_detail_brca,
    mock_study_detail_luad,
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
@patch("cbioportal_mcp.api_client.APIClient.make_api_request")
async def test_get_multiple_studies_partial_failure(
    mock_make_api_request, cbioportal_server_instance: CBioPortalMCPServer, mock_study_detail_brca
):
    server = cbioportal_server_instance
    study_ids_to_fetch = ["brca_tcga", "failed_study", "another_failed_study"]

    # Configure mock_make_api_request
    async def side_effect_func(url, *args, **kwargs):
        if "studies/brca_tcga" in url:
            return mock_study_detail_brca  # Success
        elif "studies/failed_study" in url:
            raise Exception("Simulated API error for failed_study")  # Failure 1
        elif "studies/another_failed_study" in url:
            raise ValueError(
                "Simulated internal error for another_failed_study"
            )  # Failure 2
        raise ValueError(f"Unexpected URL for _make_api_request: {url}")

    mock_make_api_request.side_effect = side_effect_func

    result = await server.get_multiple_studies(study_ids=study_ids_to_fetch)

    assert len(result["studies"]) == 3
    assert result["studies"]["brca_tcga"] == mock_study_detail_brca
    assert "error" in result["studies"]["failed_study"]
    assert (
        result["studies"]["failed_study"]["error"]
        == "Simulated API error for failed_study"
    )
    assert "error" in result["studies"]["another_failed_study"]
    assert (
        result["studies"]["another_failed_study"]["error"]
        == "Simulated internal error for another_failed_study"
    )

    assert result["metadata"]["count"] == 3
    assert result["metadata"]["errors"] == 2  # Two errors expected
    assert result["metadata"]["concurrent"] is True

    expected_calls = [
        call("studies/brca_tcga"),
        call("studies/failed_study"),
        call("studies/another_failed_study"),
    ]
    mock_make_api_request.assert_has_calls(expected_calls, any_order=True)
    assert mock_make_api_request.call_count == 3


@pytest.mark.asyncio
@patch("cbioportal_mcp.api_client.APIClient.make_api_request")
async def test_get_multiple_studies_empty_list(
    mock_make_api_request, cbioportal_server_instance: CBioPortalMCPServer
):
    server = cbioportal_server_instance
    study_ids_to_fetch = []

    result = await server.get_multiple_studies(study_ids=study_ids_to_fetch)

    assert len(result["studies"]) == 0
    assert result["metadata"]["count"] == 0
    assert result["metadata"]["errors"] == 0
    assert result["metadata"]["concurrent"] is True

    mock_make_api_request.assert_not_called()


# --- Tests for get_multiple_genes ---
@pytest.mark.asyncio
@patch("cbioportal_mcp.api_client.APIClient.make_api_request")
async def test_get_multiple_genes_single_batch_success(
    mock_make_api_request,
    cbioportal_server_instance: CBioPortalMCPServer,
    mock_gene_batch_response_page1, 
    mock_gene_detail_tp53,
    mock_gene_detail_brca1,
):
    server = cbioportal_server_instance
    gene_ids_to_fetch = ["TP53", "BRCA1"]

    mock_make_api_request.return_value = mock_gene_batch_response_page1

    result = await server.get_multiple_genes(
        gene_ids=gene_ids_to_fetch, gene_id_type="HUGO_GENE_SYMBOL"
    )

    assert len(result["genes"]) == 2
    assert result["genes"]["TP53"] == mock_gene_detail_tp53
    assert result["genes"]["BRCA1"] == mock_gene_detail_brca1
    assert result["metadata"]["count"] == 2
    assert result["metadata"]["total_requested"] == 2
    assert result["metadata"]["errors"] == 0
    assert result["metadata"]["concurrent"] is True
    assert result["metadata"]["batches"] == 1

    mock_make_api_request.assert_called_once_with(
        "genes/fetch",
        method="POST",
        params={"geneIdType": "HUGO_GENE_SYMBOL", "projection": "SUMMARY"},
        json_data=gene_ids_to_fetch,
    )


@pytest.mark.asyncio
@patch("cbioportal_mcp.api_client.APIClient.make_api_request")
async def test_get_multiple_genes_multiple_batches_success(
    mock_make_api_request,
    cbioportal_server_instance: CBioPortalMCPServer,
    mock_gene_detail_tp53,
    mock_gene_detail_brca1,
):
    server = cbioportal_server_instance
    gene_ids_to_fetch = [str(i) for i in range(1, 149)] + ["7157", "672"]

    mock_batch_1_response = [
        {"entrezGeneId": i, "hugoGeneSymbol": f"GENE{i}", "type": "protein-coding"}
        for i in range(1, 100)
    ] + [mock_gene_detail_tp53]

    mock_batch_2_response = [
        {"entrezGeneId": i, "hugoGeneSymbol": f"GENE{i}", "type": "protein-coding"}
        for i in range(100, 149)
    ] + [mock_gene_detail_brca1]

    mock_make_api_request.side_effect = [mock_batch_1_response, mock_batch_2_response]

    result = await server.get_multiple_genes(
        gene_ids=gene_ids_to_fetch, gene_id_type="ENTREZ_GENE_ID"
    )

    assert len(result["genes"]) == 150
    assert result["genes"]["7157"] == mock_gene_detail_tp53
    assert result["genes"]["672"] == mock_gene_detail_brca1
    assert result["metadata"]["count"] == 150
    assert result["metadata"]["total_requested"] == 150
    assert result["metadata"]["errors"] == 0
    assert result["metadata"]["concurrent"] is True
    assert result["metadata"]["batches"] == 2

    expected_api_calls = [
        call(
            "genes/fetch",
            method="POST",
            params={"geneIdType": "ENTREZ_GENE_ID", "projection": "SUMMARY"},
            json_data=gene_ids_to_fetch[0:100],
        ),
        call(
            "genes/fetch",
            method="POST",
            params={"geneIdType": "ENTREZ_GENE_ID", "projection": "SUMMARY"},
            json_data=gene_ids_to_fetch[100:150],
        ),
    ]
    mock_make_api_request.assert_has_calls(expected_api_calls, any_order=True)
    assert mock_make_api_request.call_count == 2


@pytest.mark.asyncio
@patch("cbioportal_mcp.api_client.APIClient.make_api_request")
async def test_get_multiple_genes_partial_batch_failure(
    mock_make_api_request, cbioportal_server_instance: CBioPortalMCPServer
):
    server = cbioportal_server_instance
    gene_ids_to_fetch = [str(i) for i in range(1, 151)]

    mock_batch_1_response = [
        {"entrezGeneId": i, "hugoGeneSymbol": f"GENE{i}", "type": "protein-coding"}
        for i in range(1, 101)
    ]

    async def side_effect_func(url, method, params, json_data):
        if json_data == gene_ids_to_fetch[0:100]:
            return mock_batch_1_response
        elif json_data == gene_ids_to_fetch[100:150]:
            raise Exception("Simulated API error for second batch")
        raise ValueError("Unexpected API call during partial failure test")

    mock_make_api_request.side_effect = side_effect_func

    result = await server.get_multiple_genes(
        gene_ids=gene_ids_to_fetch, gene_id_type="ENTREZ_GENE_ID"
    )

    assert len(result["genes"]) == 100
    assert result["genes"]["1"]["hugoGeneSymbol"] == "GENE1"
    assert result["genes"]["100"]["hugoGeneSymbol"] == "GENE100"
    assert "101" not in result["genes"]

    assert result["metadata"]["count"] == 100
    assert result["metadata"]["total_requested"] == 150
    assert result["metadata"]["errors"] == 1
    assert result["metadata"]["concurrent"] is True
    assert result["metadata"]["batches"] == 2

    expected_api_calls = [
        call(
            "genes/fetch",
            method="POST",
            params={"geneIdType": "ENTREZ_GENE_ID", "projection": "SUMMARY"},
            json_data=gene_ids_to_fetch[0:100],
        ),
        call(
            "genes/fetch",
            method="POST",
            params={"geneIdType": "ENTREZ_GENE_ID", "projection": "SUMMARY"},
            json_data=gene_ids_to_fetch[100:150],
        ),
    ]
    mock_make_api_request.assert_has_calls(expected_api_calls, any_order=True)
    assert mock_make_api_request.call_count == 2


@pytest.mark.asyncio
@patch("cbioportal_mcp.api_client.APIClient.make_api_request")
async def test_get_multiple_genes_empty_list(
    mock_make_api_request, cbioportal_server_instance: CBioPortalMCPServer
):
    server = cbioportal_server_instance
    gene_ids_to_fetch = []

    result = await server.get_multiple_genes(
        gene_ids=gene_ids_to_fetch, gene_id_type="ENTREZ_GENE_ID"
    )

    assert len(result["genes"]) == 0
    assert result["metadata"]["count"] == 0
    assert result["metadata"]["total_requested"] == 0
    assert result["metadata"]["errors"] == 0
    assert result["metadata"]["concurrent"] is True
    assert result["metadata"]["batches"] == 0

    mock_make_api_request.assert_not_called()


# More tests for get_multiple_genes will go here
