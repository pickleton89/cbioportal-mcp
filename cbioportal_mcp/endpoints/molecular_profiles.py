"""
Molecular profiles endpoint module for the cBioPortal MCP server.

Contains all molecular profile and clinical data related endpoint methods:
- get_molecular_profiles: Get molecular profiles for a study
- get_clinical_data: Get clinical data for patients
- get_gene_panels_for_study: Get gene panels for a study
- get_gene_panel_details: Get detailed gene panel information
"""

from typing import Any, Dict, List, Optional, Union

import httpx
from ..api_client import APIClient
from ..constants import FETCH_ALL_PAGE_SIZE
from .base import handle_api_errors
from ..utils.validation import (
    validate_page_params,
    validate_sort_params,
    validate_study_id,
)
from ..utils.pagination import collect_all_results
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MolecularProfilesEndpoints:
    """Handles all molecular profile and clinical data endpoints for the cBioPortal MCP server."""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client


    @handle_api_errors("get molecular profiles")
    async def get_molecular_profiles(
        self,
        study_id: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """
        Get a list of molecular profiles available for a specific cancer study with pagination support.
        """
        # Input Validation
        validate_study_id(study_id)
        validate_page_params(page_number, page_size, limit)
        validate_sort_params(sort_by, direction)

        try:
            if limit == 0:
                page_size = FETCH_ALL_PAGE_SIZE
            profiles = await self.api_client.make_api_request(
                f"studies/{study_id}/molecular-profiles"
            )
            if sort_by:
                reverse = direction.upper() == "DESC"
                profiles.sort(key=lambda p: str(p.get(sort_by, "")), reverse=reverse)
            total_count = len(profiles)
            start_idx = page_number * page_size
            end_idx = start_idx + page_size
            paginated_profiles = profiles[start_idx:end_idx]
            if limit and limit > 0 and len(paginated_profiles) > limit:
                paginated_profiles = paginated_profiles[:limit]
            has_more = end_idx < total_count
            return {
                "molecular_profiles": paginated_profiles,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_count,
                    "has_more": has_more,
                },
            }
        except Exception as e:
            return {
                "error": f"Failed to get molecular profiles for {study_id}: {str(e)}"
            }

    @handle_api_errors("get clinical data")
    async def get_clinical_data(
        self,
        study_id: str,
        attribute_ids: Optional[List[str]] = None,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """
        Get clinical data for patients in a study with pagination support. Can fetch specific attributes or all.
        """
        try:
            api_call_params = {
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction,
                "clinicalDataType": "PATIENT",  # Assuming PATIENT level data
            }
            if sort_by:
                api_call_params["sortBy"] = sort_by
            if limit == 0:
                api_call_params["pageSize"] = FETCH_ALL_PAGE_SIZE

            clinical_data_from_api = []
            if attribute_ids:
                endpoint = f"studies/{study_id}/clinical-data/fetch"
                payload = {"attributeIds": attribute_ids, "clinicalDataType": "PATIENT"}
                clinical_data_from_api = await self.api_client.make_api_request(
                    endpoint, method="POST", params=api_call_params, json_data=payload
                )
            else:
                endpoint = f"studies/{study_id}/clinical-data"
                clinical_data_from_api = await self.api_client.make_api_request(
                    endpoint, method="GET", params=api_call_params
                )

            if (
                isinstance(clinical_data_from_api, dict)
                and "api_error" in clinical_data_from_api
            ):
                return {
                    "error": "API error fetching clinical data",
                    "details": clinical_data_from_api,
                    "request_params": api_call_params,
                }
            if not isinstance(clinical_data_from_api, list):
                return {
                    "error": "Unexpected API response type for clinical data (expected list)",
                    "details": clinical_data_from_api,
                    "request_params": api_call_params,
                }

            api_might_have_more = (
                len(clinical_data_from_api) == api_call_params["pageSize"]
            )
            if (
                api_call_params["pageSize"] == FETCH_ALL_PAGE_SIZE
                and len(clinical_data_from_api) < FETCH_ALL_PAGE_SIZE
            ):
                api_might_have_more = False

            # Apply server-side limit to the data that will be processed and returned
            data_to_process = clinical_data_from_api
            if limit and limit > 0 and len(clinical_data_from_api) > limit:
                data_to_process = clinical_data_from_api[:limit]

            by_patient = {}
            for item in data_to_process:
                patient_id = item.get("patientId")
                if patient_id:
                    if patient_id not in by_patient:
                        by_patient[patient_id] = {}
                    by_patient[patient_id][item.get("clinicalAttributeId")] = item.get(
                        "value"
                    )

            # Update total_found to be the number of unique patients, not raw data items
            # This makes the count consistent with the actual returned data structure
            total_patients = len(by_patient)

            return {
                "clinical_data_by_patient": by_patient,  # This contains unique patients with their attributes
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_patients,  # Now using patient count for consistency
                    "has_more": api_might_have_more,
                },
            }
        except Exception as e:
            return {
                "error": f"Failed to get clinical data for study {study_id}: {str(e)}"
            }

    @handle_api_errors("get gene panels for study")
    async def get_gene_panels_for_study(
        self,
        study_id: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = "genePanelId",
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get all gene panels in a specific study with pagination support.

        Args:
            study_id: The ID of the cancer study (e.g., "acc_tcga").
            page_number: Page number to retrieve (0-based).
            page_size: Number of items per page.
            sort_by: Field to sort by (e.g., "genePanelId").
            direction: Sort direction ("ASC" or "DESC").
            limit: Optional maximum number of gene panels to return. If None, fetches all available based on page_number and page_size for a single page, or all results if limit is used with collect_all_results.

        Returns:
            A list of gene panel objects, or an error dictionary.
        """
        if not study_id or not isinstance(study_id, str):
            return {"error": "study_id must be a non-empty string"}
        if not isinstance(page_number, int) or page_number < 0:
            return {"error": "page_number must be a non-negative integer"}
        if not isinstance(page_size, int) or page_size <= 0:
            return {"error": "page_size must be a positive integer"}
        if sort_by is not None and not isinstance(sort_by, str):
            # Allow empty string for sort_by if API supports it, or check against valid fields
            return {"error": "sort_by must be a string or None"}
        if direction.upper() not in ["ASC", "DESC"]:
            return {"error": "direction must be 'ASC' or 'DESC'"}
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            # Allow limit=0 to mean no results, consistent with some APIs
            return {"error": "limit must be a non-negative integer or None"}

        endpoint = f"studies/{study_id}/gene-panels"
        params = {
            "pageNumber": page_number,
            "pageSize": page_size,
            "projection": "DETAILED",  # Default to include genes in panels
            "sortBy": sort_by,
            "direction": direction.upper(),
        }
        # Remove None params, especially sortBy if not provided
        params = {k: v for k, v in params.items() if v is not None}

        try:
            if limit is not None:
                # collect_all_results handles pagination internally up to the limit
                return await collect_all_results(
                    self.api_client, endpoint, params=params, limit=limit
                )
            else:
                # Fetch a single page as defined by page_number and page_size
                return await self.api_client.make_api_request(endpoint, params=params)
        except httpx.HTTPStatusError as e:
            logger.error(
                f"API error getting gene panels for study {study_id}: {e.response.status_code} - {e.response.text}"
            )
            return {
                "error": f"API error: {e.response.status_code}",
                "details": e.response.text,
            }
        except httpx.RequestError as e:
            logger.error(f"Request error getting gene panels for study {study_id}: {e}")
            return {"error": "Request error", "details": str(e)}
        except Exception as e:
            logger.error(
                f"Unexpected error getting gene panels for study {study_id}: {e}",
                exc_info=True,
            )
            return {"error": "Unexpected server error", "details": str(e)}

    @handle_api_errors("get gene panel details")
    async def get_gene_panel_details(
        self,
        gene_panel_id: str,
        projection: str = "DETAILED",
    ) -> Dict[str, Any]:
        """
        Get detailed information for a specific gene panel, including the list of genes.

        Args:
            gene_panel_id: The ID of the gene panel (e.g., "IMPACT341").
            projection: Level of detail ("ID", "SUMMARY", "DETAILED", "META").
                        "DETAILED" includes the list of genes.

        Returns:
            A dictionary containing gene panel details, or an error dictionary.
        """
        if not gene_panel_id or not isinstance(gene_panel_id, str):
            return {"error": "gene_panel_id must be a non-empty string"}
        if projection.upper() not in ["ID", "SUMMARY", "DETAILED", "META"]:
            return {
                "error": "projection must be one of 'ID', 'SUMMARY', 'DETAILED', 'META'"
            }

        endpoint = "gene-panels/fetch"
        # API requires query param for projection, and POST body for IDs
        params = {"projection": projection.upper()}
        request_body = [gene_panel_id]  # API expects a list of gene panel IDs

        try:
            results = await self.api_client.make_api_request(
                endpoint, method="POST", params=params, json_data=request_body
            )

            # The API returns a list, even for a single ID request
            if isinstance(results, list):
                if len(results) > 0:
                    return results[
                        0
                    ]  # Return the first (and expected only) gene panel object
                else:
                    # Successfully queried, but no panel found for this ID
                    return {
                        "error": "Gene panel not found",
                        "gene_panel_id": gene_panel_id,
                    }
            else:
                # This case implies an unexpected API response format (not a list)
                logger.warning(
                    f"Unexpected response format for get_gene_panel_details {gene_panel_id}: {type(results)}"
                )
                return {
                    "error": "Unexpected response format from API",
                    "details": str(results),
                }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"API error getting gene panel details for {gene_panel_id}: {e.response.status_code} - {e.response.text}"
            )
            return {
                "error": f"API error: {e.response.status_code}",
                "details": e.response.text,
            }
        except httpx.RequestError as e:
            logger.error(
                f"Request error getting gene panel details for {gene_panel_id}: {e}"
            )
            return {"error": "Request error", "details": str(e)}
        except Exception as e:
            logger.error(
                f"Unexpected error getting gene panel details for {gene_panel_id}: {e}",
                exc_info=True,
            )
            return {"error": "Unexpected server error", "details": str(e)}
