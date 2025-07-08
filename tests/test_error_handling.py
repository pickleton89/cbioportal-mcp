#!/usr/bin/env python3
# Tests for generic API error handling in the cBioPortal MCP Server

import pytest
from unittest.mock import patch
import httpx



@pytest.mark.parametrize(
    "method_name_to_test, method_args, method_kwargs, exception_to_raise, expected_error_prefix",
    [
        (
            "get_study_details",
            ("non_existent_study",),  # args tuple
            {},  # kwargs dict
            httpx.HTTPStatusError(
                message="404 Client Error: Not Found for url: /api/studies/non_existent_study",
                request=httpx.Request("GET", "/api/studies/non_existent_study"),
                response=httpx.Response(
                    404, request=httpx.Request("GET", "/api/studies/non_existent_study")
                ),
            ),
            "Failed to get study details for non_existent_study",
        ),
        (
            "get_cancer_studies",
            (),  # args tuple
            {"page_number": 0, "page_size": 10},  # kwargs dict
            httpx.RequestError(
                message="Timeout occurred while requesting /api/studies",
                request=httpx.Request("GET", "/api/studies"),
            ),
            "Failed to get cancer studies",
        ),
        (
            "get_molecular_profiles",
            ("study_123",),  # args: study_id
            {"page_number": 0, "page_size": 10},  # kwargs
            httpx.HTTPStatusError(
                message="500 Server Error: Internal Server Error for url: /api/studies/study_123/molecular-profiles",
                request=httpx.Request(
                    "GET", "/api/studies/study_123/molecular-profiles"
                ),
                response=httpx.Response(
                    500,
                    request=httpx.Request(
                        "GET", "/api/studies/study_123/molecular-profiles"
                    ),
                ),
            ),
            "Failed to get molecular profiles for study_123",
        ),
        (
            "get_genes",
            (["TP53"],),  # args: gene_ids as a list
            {"gene_id_type": "HUGO_SYMBOL", "projection": "SUMMARY"},  # kwargs
            httpx.RequestError(
                message="Network error while fetching gene TP53",
                request=httpx.Request(
                    "GET", "/api/genes/fetch"
                ),
            ),
            "Failed to get gene information",
        ),
        (
            "get_clinical_data",
            ("study_forbidden",),  # args: study_id
            {},  # kwargs: no attribute_ids, fetch all
            httpx.HTTPStatusError(
                message="403 Client Error: Forbidden for url: /api/studies/study_forbidden/clinical-data",
                request=httpx.Request(
                    "GET", "/api/studies/study_forbidden/clinical-data"
                ),
                response=httpx.Response(
                    403,
                    request=httpx.Request(
                        "GET", "/api/studies/study_forbidden/clinical-data"
                    ),
                ),
            ),
            "Failed to get clinical data for study study_forbidden",
        ),
        (
            "get_clinical_data",
            ("study_network_error",),  # args: study_id
            {"attribute_ids": ["ATTR1", "ATTR2"]},  # kwargs: specific attributes
            httpx.RequestError(
                message="Network error while fetching clinical data for study_network_error",
                request=httpx.Request(
                    "POST", "/api/studies/study_network_error/clinical-data/fetch"
                ),
            ),
            "Failed to get clinical data for study study_network_error",
        ),
    ],
)
@patch("api_client.APIClient.make_api_request")
@pytest.mark.asyncio
async def test_generic_api_error_handling(
    mock_make_api_request,
    cbioportal_server_instance, # This fixture is defined in conftest.py
    method_name_to_test,
    method_args,
    method_kwargs,
    exception_to_raise,
    expected_error_prefix,
):
    """Test generic error handling for API calls that raise httpx exceptions."""
    server = cbioportal_server_instance
    mock_make_api_request.side_effect = exception_to_raise

    method_to_call = getattr(server, method_name_to_test)

    actual_args = []
    if (
        method_name_to_test == "get_genes"
        and len(method_args) == 1
        and isinstance(method_args[0], tuple)
    ):
        actual_args = list(
            method_args[0]
        )
    else:
        actual_args = list(method_args)

    result = await method_to_call(*actual_args, **method_kwargs)

    assert "error" in result, (
        f"Result should contain an error key for {method_name_to_test}"
    )
    assert expected_error_prefix in result["error"], (
        f"Error message for {method_name_to_test} did not contain expected prefix '{expected_error_prefix}'. Got: {result['error']}"
    )

    assert (
        str(
            exception_to_raise.args[0]
            if exception_to_raise.args
            else str(exception_to_raise)
        )
        in result["error"]
    ), (
        f"Error message for {method_name_to_test} did not contain the original exception message. Got: {result['error']}"
    )

    assert mock_make_api_request.called, (
        f"_make_api_request was not called for {method_name_to_test}"
    )
