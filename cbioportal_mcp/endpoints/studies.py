"""
Studies endpoint module for the cBioPortal MCP server.

Contains all study-related endpoint methods:
- get_cancer_studies: List cancer studies with pagination
- search_studies: Search studies by keyword  
- get_study_details: Get detailed study information
- get_multiple_studies: Fetch multiple studies concurrently
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx
from ..api_client import APIClient
from ..utils.validation import (
    validate_page_params,
    validate_sort_params, 
    validate_study_id,
    validate_keyword,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class StudiesEndpoints:
    """Handles all study-related endpoints for the cBioPortal MCP server."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def collect_all_results(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        method: str = "GET",
        json_data: Any = None,
    ) -> List[Dict[str, Any]]:
        """Collect all results from a paginated endpoint."""
        # This is a temporary method - should be moved to utils in future
        from ..utils.pagination import collect_all_results
        return await collect_all_results(
            self.api_client, endpoint, params, method, json_data
        )

    async def get_cancer_studies(
        self,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of cancer studies in cBioPortal with pagination support.

        Args:
            page_number: Page number to retrieve (0-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            direction: Sort direction (ASC or DESC)
            limit: Maximum number of items to return across all pages (None for no limit)

        Returns:
            Dictionary containing list of studies and metadata
        """
        # Input Validation
        validate_page_params(page_number, page_size, limit)
        validate_sort_params(sort_by, direction)

        try:
            # Configure API parameters
            api_params = {
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction,
            }
            if sort_by:
                api_params["sortBy"] = sort_by

            # Special behavior for limit=0 (fetch all results)
            if limit == 0:
                # Use the collect_all_results helper which handles pagination automatically
                studies_from_api = await self.collect_all_results(
                    "studies", params=api_params
                )
                studies_for_response = studies_from_api
                has_more = False  # We fetched everything
            else:
                # Fetch just the requested page
                studies_from_api = await self.api_client.make_api_request(
                    "studies", params=api_params
                )

                # Apply the limit if specified and smaller than the page results
                studies_for_response = studies_from_api
                if limit and 0 < limit < len(studies_from_api):
                    studies_for_response = studies_from_api[:limit]

                # Determine if there might be more data available
                has_more = len(studies_from_api) == page_size

            # Count the actual items we're returning
            total_items = len(studies_for_response)

            return {
                "studies": studies_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_items,
                    "has_more": has_more,
                },
            }
        except Exception as e:
            return {"error": f"Failed to get cancer studies: {str(e)}"}

    async def search_studies(
        self,
        keyword: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search for cancer studies by keyword in their name or description with pagination support.

        Args:
            keyword: Keyword to search for
            page_number: Page number to retrieve (0-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            direction: Sort direction (ASC or DESC)
            limit: Maximum number of items to return across all pages (None for no limit)

        Returns:
            Dictionary containing list of studies and metadata
        """
        # Input Validation
        validate_keyword(keyword)
        validate_page_params(page_number, page_size, limit)
        validate_sort_params(sort_by, direction)

        try:
            # Await the asynchronous API call
            all_studies = await self.api_client.make_api_request("studies")

            if not isinstance(all_studies, list):
                # Handle cases where API request might not return a list (e.g., error response)
                error_message = (
                    "Unexpected response from API when fetching all studies."
                )
                if isinstance(all_studies, dict) and "error" in all_studies:
                    error_message = all_studies["error"]
                return {
                    "error": f"Failed to search studies for '{keyword}': {error_message}"
                }

            keyword_lower = keyword.lower()
            matching_studies = [
                study
                for study in all_studies
                if keyword_lower in study.get("name", "").lower()
                or keyword_lower in study.get("description", "").lower()
            ]

            if sort_by:
                reverse = direction.upper() == "DESC"
                matching_studies.sort(
                    key=lambda s: str(s.get(sort_by, "")), reverse=reverse
                )

            total_count = len(matching_studies)
            start_idx = page_number * page_size
            end_idx = start_idx + page_size
            paginated_studies = matching_studies[start_idx:end_idx]

            if limit and limit > 0 and len(paginated_studies) > limit:
                paginated_studies = paginated_studies[:limit]

            has_more = end_idx < total_count

            return {
                "studies": paginated_studies,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size
                    if limit != 0
                    else total_count,  # Adjust page_size if all were requested
                    "total_found": total_count,
                    "has_more": has_more
                    if limit != 0
                    else False,  # No more if all were requested
                },
            }
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"Failed to search studies for '{keyword}': API request failed with status {exc.response.status_code}"
            }
        except httpx.RequestError as exc:
            return {
                "error": f"Failed to search studies for '{keyword}': Network error - {str(exc)}"
            }
        except Exception as e:
            return {
                "error": f"Failed to search studies for '{keyword}': An unexpected error occurred - {str(e)}"
            }

    async def get_study_details(self, study_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific cancer study.

        Args:
            study_id: The ID of the cancer study

        Returns:
            Dictionary containing study details
        """
        # Input Validation
        validate_study_id(study_id)

        endpoint = f"studies/{study_id}"
        try:
            study = await self.api_client.make_api_request(endpoint)
            return {"study": study}
        except Exception as e:
            return {"error": f"Failed to get study details for {study_id}: {str(e)}"}

    async def get_multiple_studies(self, study_ids: List[str]) -> Dict:
        """
        Get details for multiple studies concurrently.

        This method demonstrates the power of async concurrency by fetching
        multiple studies in parallel, which is much faster than sequential requests.

        Args:
            study_ids: List of study IDs to fetch

        Returns:
            Dictionary mapping study IDs to their details, with metadata about the operation
        """
        if not study_ids:
            return {
                "studies": {},
                "metadata": {"count": 0, "errors": 0, "concurrent": True},
            }

        # Create a reusable async function for fetching a single study
        async def fetch_study(study_id):
            try:
                data = await self.api_client.make_api_request(f"studies/{study_id}")
                return {"study_id": study_id, "data": data, "success": True}
            except Exception as e:
                return {"study_id": study_id, "error": str(e), "success": False}

        # Create tasks for all study IDs and run them concurrently
        tasks = [fetch_study(study_id) for study_id in study_ids]
        start_time = time.perf_counter()
        # Use asyncio.gather to execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        end_time = time.perf_counter()

        # Process results into a structured response
        studies_dict = {}
        error_count = 0

        for result in results:
            if result["success"]:
                studies_dict[result["study_id"]] = result["data"]
            else:
                studies_dict[result["study_id"]] = {"error": result["error"]}
                error_count += 1

        return {
            "studies": studies_dict,
            "metadata": {
                "count": len(study_ids),
                "errors": error_count,
                "execution_time": round(end_time - start_time, 3),
                "concurrent": True,
            },
        }

    async def get_cancer_types(
        self,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """
        Get a list of all available cancer types in cBioPortal with pagination support.

        Args:
            page_number: Page number (0-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            direction: Sort direction (ASC or DESC)
            limit: Maximum number of items to return across all pages (None for no limit)

        Returns:
            Dictionary containing list of cancer types and metadata
        """
        # Input Validation
        validate_page_params(page_number, page_size, limit)
        validate_sort_params(sort_by, direction)

        try:
            # Configure API parameters
            api_params = {
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction,
            }
            if sort_by:
                api_params["sortBy"] = sort_by

            # Special behavior for limit=0 (fetch all results)
            if limit == 0:
                # Use the collect_all_results helper for automatic pagination
                types_from_api = await self.collect_all_results(
                    "cancer-types", params=api_params
                )
                types_for_response = types_from_api
                has_more = False  # We fetched everything
            else:
                # Fetch just the requested page
                types_from_api = await self.api_client.make_api_request(
                    "cancer-types", params=api_params
                )

                # Apply the limit if specified and smaller than the page results
                types_for_response = types_from_api
                if limit and 0 < limit < len(types_from_api):
                    types_for_response = types_from_api[:limit]

                # Determine if there might be more data available
                has_more = len(types_from_api) == page_size

            # Count the actual items we're returning
            total_items = len(types_for_response)

            return {
                "cancer_types": types_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_items,
                    "has_more": has_more,
                },
            }
        except Exception as e:
            return {"error": f"Failed to get cancer types: {str(e)}"}
