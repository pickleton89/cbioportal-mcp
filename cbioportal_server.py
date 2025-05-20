#!/usr/bin/env python3
"""
cBioPortal MCP Server (clean implementation)
Provides Model Context Protocol tools for accessing the cBioPortal API with full pagination support.
"""

import argparse
import asyncio
import logging
import signal
import sys
from typing import Any, Dict, List, Optional, AsyncGenerator

import httpx
from fastmcp import FastMCP
from api_client import APIClient # Changed from relative for test compatibility

# Ensure project root is in sys.path for utility imports if needed
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from utils.pagination_utils import paginate_results, collect_all_results # Example if utils were used

logger = logging.getLogger(__name__)


class CBioPortalMCPServer:
    """MCP Server for interacting with the cBioPortal API."""

    def __init__(self, base_url: str = "https://www.cbioportal.org/api", client_timeout: float = 480.0):
        self.base_url = base_url.rstrip('/') # Ensure no trailing slash
        # self.client = None # Removed
        self.api_client = APIClient(base_url=self.base_url, client_timeout=client_timeout) # Added, using existing 480s timeout
        self.mcp = FastMCP(
            name="cBioPortal",
            description="Access cancer genomics data from cBioPortal",
            instructions="This server provides tools to access and analyze cancer genomics data from cBioPortal.",
        )

        # Register lifecycle hooks
        self.mcp.on_startup = [self.startup]
        self.mcp.on_shutdown = [self.shutdown]

        # Register tools
        self._register_tools()

    async def startup(self):
        """Initialize async resources when server starts."""
        # self.client = httpx.AsyncClient(timeout=480.0) # Removed
        await self.api_client.startup() # Added
        logger.info("cBioPortal MCP Server started, APIClient initialized.") # Updated log

    async def shutdown(self):
        """Clean up async resources when server shuts down."""
        # if self.client: # Removed block
        #     await self.client.aclose()
        #     logger.info("cBioPortal MCP Server async HTTP client closed")
        if hasattr(self, 'api_client') and self.api_client: # Added
            await self.api_client.shutdown()
            logger.info("cBioPortal MCP Server APIClient shut down.") # Updated log
        else: # Added for completeness
            logger.info("cBioPortal MCP Server APIClient was not available or already shut down.")

    def _register_tools(self):
        """Dynamically register public methods as MCP tools."""
        for name in dir(self):
            if not name.startswith("_") and name not in [
                "startup",
                "shutdown",
                "mcp",
                "client",
                "base_url",
            ]:
                method = getattr(self, name)
                if callable(method):
                    self.mcp.add_tool(method)
                    logger.debug(f"Registered tool: {name}")

    async def paginate_results(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        method: str = "GET",
        json_data: Any = None,
        max_pages: int = None,
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Asynchronous generator that yields pages of results from paginated API endpoints.

        Args:
            endpoint: API endpoint path
            params: Query parameters to include in the request
            method: HTTP method (GET or POST)
            json_data: JSON data for POST requests
            max_pages: Maximum number of pages to retrieve (None for all available)

        Yields:
            Lists of results, one page at a time
        """
        if params is None:
            params = {}

        # Ensure we have pagination parameters
        page = params.get("pageNumber", 0)
        page_size = params.get("pageSize", 50)

        # Set pagination parameters in the request
        request_params = params.copy()

        page_count = 0
        has_more = True

        while has_more and (max_pages is None or page_count < max_pages):
            # Update page number for current request
            request_params["pageNumber"] = page

            # Make the API request
            results = await self.api_client.make_api_request( # Changed
                endpoint,
                method=method,
                params=request_params.copy(),
                json_data=json_data,
            )

            # Check if we got any results
            if not results or len(results) == 0:
                break

            yield results

            # Check if we have more pages
            has_more = len(results) == page_size

            # Increment counters
            page += 1
            page_count += 1

    async def collect_all_results(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        method: str = "GET",
        json_data: Any = None,
        max_pages: int = None,
        limit: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Collect all results from a paginated endpoint into a single list.

        Args:
            endpoint: API endpoint path
            params: Query parameters to include in the request
            method: HTTP method (GET or POST)
            json_data: JSON data for POST requests
            max_pages: Maximum number of pages to retrieve
            limit: Maximum number of total results to return

        Returns:
            List of all collected results (limited by max_pages and/or limit)
        """
        all_results = []

        async for page in self.paginate_results(
            endpoint, params, method, json_data, max_pages
        ):
            all_results.extend(page)

            # Stop if we've reached the specified limit
            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break

        return all_results

    # _make_api_request method was removed.
    # Its functionality is now handled by the APIClient class in api_client.py.


    # --- Collection-returning methods with pagination ---

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
        if not isinstance(page_number, int):
            raise TypeError("page_number must be an integer")
        if page_number < 0:
            raise ValueError("page_number must be non-negative")
        if not isinstance(page_size, int):
            raise TypeError("page_size must be an integer")
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        if sort_by is not None and not isinstance(sort_by, str):
            raise TypeError("sort_by must be a string if provided")
        if not isinstance(direction, str) or direction.upper() not in ["ASC", "DESC"]:
            raise ValueError("direction must be 'ASC' or 'DESC'")
        if limit is not None:
            if not isinstance(limit, int):
                raise TypeError("limit must be an integer if provided")
            if limit < 0:
                raise ValueError("limit must be non-negative if provided")

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
        if not isinstance(page_number, int):
            raise TypeError("page_number must be an integer")
        if page_number < 0:
            raise ValueError("page_number must be non-negative")
        if not isinstance(page_size, int):
            raise TypeError("page_size must be an integer")
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        if sort_by is not None and not isinstance(sort_by, str):
            raise TypeError("sort_by must be a string if provided")
        if not isinstance(direction, str) or direction.upper() not in ["ASC", "DESC"]:
            raise ValueError("direction must be 'ASC' or 'DESC'")
        if limit is not None:
            if not isinstance(limit, int):
                raise TypeError("limit must be an integer if provided")
            if limit < 0:
                raise ValueError("limit must be non-negative if provided")

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

    async def get_samples_in_study(
        self,
        study_id: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """
        Get a list of samples associated with a specific cancer study with pagination support.
        """
        # Input Validation
        if not isinstance(study_id, str):
            raise TypeError("study_id must be a string")
        if not study_id:
            raise ValueError("study_id cannot be empty")
        if not isinstance(page_number, int):
            raise TypeError("page_number must be an integer")
        if page_number < 0:
            raise ValueError("page_number must be non-negative")
        if not isinstance(page_size, int):
            raise TypeError("page_size must be an integer")
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        if sort_by is not None and not isinstance(sort_by, str):
            raise TypeError("sort_by must be a string if provided")
        if not isinstance(direction, str) or direction.upper() not in ["ASC", "DESC"]:
            raise ValueError("direction must be 'ASC' or 'DESC'")
        if limit is not None:
            if not isinstance(limit, int):
                raise TypeError("limit must be an integer if provided")
            if limit < 0:
                raise ValueError("limit must be non-negative if provided")

        try:
            api_call_params = {
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction,
            }
            if sort_by:
                api_call_params["sortBy"] = sort_by
            if limit == 0:
                api_call_params["pageSize"] = 10000000

            samples_from_api = await self.api_client.make_api_request(
                f"studies/{study_id}/samples", params=api_call_params
            )

            api_might_have_more = len(samples_from_api) == api_call_params["pageSize"]
            if (
                api_call_params["pageSize"] == 10000000
                and len(samples_from_api) < 10000000
            ):
                api_might_have_more = False

            samples_for_response = samples_from_api
            if limit and limit > 0 and len(samples_from_api) > limit:
                samples_for_response = samples_from_api[:limit]

            total_items_in_response = len(samples_for_response)

            return {
                "samples": samples_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_items_in_response,
                    "has_more": api_might_have_more,
                },
            }
        except Exception as e:
            return {"error": f"Failed to get samples for study {study_id}: {str(e)}"}

    async def search_genes(
        self,
        keyword: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """
        Search for genes by keyword in their symbol or name with pagination support.
        """
        # Input Validation
        if not isinstance(keyword, str):
            raise TypeError("keyword must be a string")
        if not keyword:
            raise ValueError("keyword cannot be empty")
        if not isinstance(page_number, int):
            raise TypeError("page_number must be an integer")
        if page_number < 0:
            raise ValueError("page_number must be non-negative")
        if not isinstance(page_size, int):
            raise TypeError("page_size must be an integer")
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        if sort_by is not None and not isinstance(sort_by, str):
            raise TypeError("sort_by must be a string if provided")
        if not isinstance(direction, str) or direction.upper() not in ["ASC", "DESC"]:
            raise ValueError("direction must be 'ASC' or 'DESC'")
        if limit is not None:
            if not isinstance(limit, int):
                raise TypeError("limit must be an integer if provided")
            if limit < 0:
                raise ValueError("limit must be non-negative if provided")

        try:
            api_call_params = {
                "keyword": keyword,
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction,
            }
            if sort_by:
                api_call_params["sortBy"] = sort_by
            if limit == 0:
                api_call_params["pageSize"] = 10000000

            genes_from_api = await self.api_client.make_api_request(
                "genes", params=api_call_params
            )  # Corrected endpoint

            # Determine if the API might have more data
            api_might_have_more = len(genes_from_api) == api_call_params["pageSize"]
            # If 'fetch all' was intended and API returned less than max fetch size, then it's definitely the end.
            if (
                api_call_params["pageSize"] == 10000000
                and len(genes_from_api) < 10000000
            ):
                api_might_have_more = False

            # Apply server-side limit if specified (after fetching the page from API)
            genes_for_response = genes_from_api
            if limit and limit > 0 and len(genes_from_api) > limit:
                genes_for_response = genes_from_api[:limit]

            # total_found in pagination now means number of items in this specific response payload
            # This makes the count consistent with the actual returned data structure
            total_items_in_response = len(genes_for_response)

            return {
                "genes": genes_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,  # Report original requested page_size to client
                    "total_found": total_items_in_response,
                    "has_more": api_might_have_more,
                },
            }
        except Exception as e:
            return {"error": f"Failed to search genes: {str(e)}"}

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
        if not isinstance(keyword, str):
            raise TypeError("keyword must be a string")
        if not keyword:
            raise ValueError("keyword cannot be empty")
        if not isinstance(page_number, int):
            raise TypeError("page_number must be an integer")
        if page_number < 0:
            raise ValueError("page_number must be non-negative")
        if not isinstance(page_size, int):
            raise TypeError("page_size must be an integer")
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        if sort_by is not None and not isinstance(sort_by, str):
            raise TypeError("sort_by must be a string if provided")
        if not isinstance(direction, str) or direction.upper() not in ["ASC", "DESC"]:
            raise ValueError("direction must be 'ASC' or 'DESC'")
        if limit is not None:
            if not isinstance(limit, int):
                raise TypeError("limit must be an integer if provided")
            if limit < 0:
                raise ValueError("limit must be non-negative if provided")

        try:
            # Consider if fetching ALL studies upfront is efficient for large datasets.
            # If the API supports server-side filtering by keyword, that would be more performant.
            # For now, assuming client-side filtering is necessary.
            # If limit == 0 means 'no limit imposed by this function call',
            # but we still need to consider practical limits for fetching 'all_studies'.
            # The previous large page_size for limit=0 could be an issue if 'studies' endpoint doesn't paginate by itself.

            # Await the asynchronous API call
            all_studies = await self.api_client.make_api_request("studies")

            if not isinstance(all_studies, list):
                # Handle cases where API request might not return a list (e.g., error response)
                # This helps prevent the 'coroutine not iterable' if _make_api_request itself has an issue
                # and doesn't raise an exception but returns something unexpected.
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

            # If limit was 0 (meaning user wanted all results), ensure page_size for response reflects total_count
            # and has_more is false, page_number is 0.
            # However, the current logic seems to imply limit=0 should still paginate based on original page_size
            # after fetching everything, which is a bit unusual. The user might expect all results in one go.
            # For now, retaining original pagination logic after fetching all.
            # If limit == 0 was used to fetch all, the pagination info might be misleading.
            # A better approach for limit=0 might be to return all matching_studies directly without pagination dict.

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
            # Log the specific HTTP error
            # import logging
            # logging.error(f"HTTP error in search_studies for '{keyword}': {exc.response.status_code} - {exc.response.text}", exc_info=True)
            return {
                "error": f"Failed to search studies for '{keyword}': API request failed with status {exc.response.status_code}"
            }
        except httpx.RequestError as exc:
            # Log network-related errors
            # import logging
            # logging.error(f"Request error in search_studies for '{keyword}': {str(exc)}", exc_info=True)
            return {
                "error": f"Failed to search studies for '{keyword}': Network error - {str(exc)}"
            }
        except Exception as e:
            # Log the exception here as well for better debugging
            # import logging
            # logging.error(f"Unexpected error in search_studies for '{keyword}': {str(e)}", exc_info=True)
            return {
                "error": f"Failed to search studies for '{keyword}': An unexpected error occurred - {str(e)}"
            }

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
        if not isinstance(study_id, str):
            raise TypeError("study_id must be a string")
        if not study_id:
            raise ValueError("study_id cannot be empty")
        if not isinstance(page_number, int):
            raise TypeError("page_number must be an integer")
        if page_number < 0:
            raise ValueError("page_number must be non-negative")
        if not isinstance(page_size, int):
            raise TypeError("page_size must be an integer")
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        if sort_by is not None and not isinstance(sort_by, str):
            raise TypeError("sort_by must be a string if provided")
        if not isinstance(direction, str) or direction.upper() not in ["ASC", "DESC"]:
            raise ValueError("direction must be 'ASC' or 'DESC'")
        if limit is not None:
            if not isinstance(limit, int):
                raise TypeError("limit must be an integer if provided")
            if limit < 0:
                raise ValueError("limit must be non-negative if provided")

        try:
            if limit == 0:
                page_size = 10000000
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

    async def get_mutations_in_gene(
        self,
        gene_id: str,
        study_id: str,
        sample_list_id: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """
        Get mutations in a specific gene for a given study and sample list, with pagination support.
        Uses the /molecular-profiles/{molecularProfileId}/mutations endpoint with GET and query parameters.
        The molecularProfileId is dynamically determined based on the studyId.
        """
        try:
            molecular_profiles_response = await self.api_client.make_api_request(
                f"studies/{study_id}/molecular-profiles"
            )
            if (
                isinstance(molecular_profiles_response, dict)
                and "api_error" in molecular_profiles_response
            ):
                return {
                    "error": f"Failed to fetch molecular profiles for study {study_id} to find mutation profile",
                    "details": molecular_profiles_response,
                }

            mutation_profile_id = None
            if isinstance(molecular_profiles_response, list):
                for profile in molecular_profiles_response:
                    if profile.get("molecularAlterationType") == "MUTATION_EXTENDED":
                        mutation_profile_id = profile.get("molecularProfileId")
                        break

            if not mutation_profile_id:
                return {
                    "error": f"No MUTATION_EXTENDED molecular profile found for study {study_id}"
                }

            api_call_params = {
                "studyId": study_id,
                "sampleListId": sample_list_id,
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction,
            }
            if sort_by:
                api_call_params["sortBy"] = sort_by
            if limit == 0:
                api_call_params["pageSize"] = 10000000

            if str(gene_id).isdigit():
                api_call_params["entrezGeneId"] = gene_id
            else:
                api_call_params["hugoGeneSymbol"] = gene_id

            endpoint = f"molecular-profiles/{mutation_profile_id}/mutations"
            mutations_from_api = await self.api_client.make_api_request(
                endpoint, method="GET", params=api_call_params
            )

            if (
                isinstance(mutations_from_api, dict)
                and "api_error" in mutations_from_api
            ):
                return {
                    "error": "API error fetching mutations",
                    "details": mutations_from_api,
                    "request_params": api_call_params,
                }
            if not isinstance(mutations_from_api, list):
                return {
                    "error": "Unexpected API response type for mutations (expected list)",
                    "details": mutations_from_api,
                    "request_params": api_call_params,
                }

            api_might_have_more = len(mutations_from_api) == api_call_params["pageSize"]
            if (
                api_call_params["pageSize"] == 10000000
                and len(mutations_from_api) < 10000000
            ):
                api_might_have_more = False

            mutations_for_response = mutations_from_api
            if limit and limit > 0 and len(mutations_from_api) > limit:
                mutations_for_response = mutations_from_api[:limit]

            total_items_in_response = len(mutations_for_response)

            return {
                "mutations": mutations_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_items_in_response,
                    "has_more": api_might_have_more,
                },
            }
        except Exception as e:
            return {
                "error": f"An unexpected error occurred in get_mutations_in_gene: {str(e)}"
            }

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
                api_call_params["pageSize"] = 10000000

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
                api_call_params["pageSize"] == 10000000
                and len(clinical_data_from_api) < 10000000
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

    async def get_gene_panels_for_study(
        self,
        study_id: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = "genePanelId",
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
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
                return await self.collect_all_results(
                    endpoint, params=params, limit=limit
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

    # --- Bulk Operations with Concurrency ---

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
        start_time = asyncio.get_event_loop().time()
        # Use asyncio.gather to execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

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

    async def get_multiple_genes(
        self,
        gene_ids: List[str],
        gene_id_type: str = "ENTREZ_GENE_ID",
        projection: str = "SUMMARY",
    ) -> Dict:
        """
        Get information about multiple genes concurrently.

        This method uses concurrency to fetch multiple genes in parallel,
        which is much more efficient than sequential requests for large batches.

        Args:
            gene_ids: List of gene IDs (Entrez IDs or Hugo symbols)
            gene_id_type: Type of gene ID provided (ENTREZ_GENE_ID or HUGO_GENE_SYMBOL)
            projection: Level of detail to return (ID, SUMMARY, DETAILED)

        Returns:
            Dictionary with gene information and performance metadata
        """
        import time

        overall_start_time = time.time()  # Single start time for the whole operation
        if not gene_ids:
            return {
                "genes": {},
                "metadata": {
                    "count": 0,
                    "total_requested": 0,
                    "errors": 0,
                    "concurrent": True,
                    "batches": 0,
                    "execution_time": round(time.time() - overall_start_time, 3),
                },
            }

        # For large gene lists, break into smaller batches for API compatibility
        batch_size = (
            100  # cBioPortal API handles batches better than very large requests
        )
        gene_batches = [
            gene_ids[i : i + batch_size] for i in range(0, len(gene_ids), batch_size)
        ]

        async def fetch_gene_batch(batch):
            try:
                params = {"geneIdType": gene_id_type, "projection": projection}
                batch_data = await self.api_client.make_api_request(
                    "genes/fetch", method="POST", params=params, json_data=batch
                )
                return {"data": batch_data, "success": True}
            except Exception as e:
                return {"error": str(e), "success": False}

        # Create tasks for all batches and run them concurrently
        tasks = [fetch_gene_batch(batch) for batch in gene_batches]
        batch_results = await asyncio.gather(*tasks)

        # Process results
        all_genes = []
        error_count = 0

        for result in batch_results:
            if result["success"]:
                all_genes.extend(result["data"])
            else:
                error_count += 1

        # Convert to dictionary for easier lookup
        genes_dict = {}
        key_field = (
            "hugoGeneSymbol" if gene_id_type == "HUGO_GENE_SYMBOL" else "entrezGeneId"
        )
        for gene in all_genes:
            gene_key_value = gene.get(key_field)
            if gene_key_value:
                genes_dict[str(gene_key_value)] = gene

        return {
            "genes": genes_dict,
            "metadata": {
                "count": len(genes_dict),
                "total_requested": len(gene_ids),
                "errors": error_count,
                "execution_time": round(time.time() - overall_start_time, 3),
                "concurrent": True,
                "batches": len(gene_batches),
            },
        }

    # --- Other methods ---

    async def get_study_details(self, study_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific cancer study.

        Args:
            study_id: The ID of the cancer study

        Returns:
            Dictionary containing study details
        """
        # Input Validation
        if not isinstance(study_id, str):
            raise TypeError("study_id must be a string")
        if not study_id:
            raise ValueError("study_id cannot be empty")

        endpoint = f"studies/{study_id}"
        try:
            study = await self.api_client.make_api_request(endpoint)
            return {"study": study}
        except Exception as e:
            return {"error": f"Failed to get study details for {study_id}: {str(e)}"}

    async def get_genes(
        self,
        gene_ids: List[str],
        gene_id_type: str = "ENTREZ_GENE_ID",
        projection: str = "SUMMARY",
    ) -> Dict:
        """
        Get information about specific genes by their Hugo symbol or Entrez ID using batch endpoint.

        Args:
            gene_ids: List of gene IDs (Entrez IDs or Hugo symbols)
            gene_id_type: Type of gene ID provided (ENTREZ_GENE_ID or HUGO_GENE_SYMBOL)
            projection: Level of detail to return (ID, SUMMARY, DETAILED)

        Returns:
            Dictionary with gene information
        """
        try:
            params = {"geneIdType": gene_id_type, "projection": projection}
            gene_data = await self.api_client.make_api_request(
                "genes/fetch", method="POST", params=params, json_data=gene_ids
            )
            return {"genes": gene_data}
        except Exception as e:
            return {"error": f"Failed to get gene information: {str(e)}"}

    async def get_sample_list_id(self, study_id: str, sample_list_id: str) -> Dict:
        return await self.api_client.make_api_request(
            f"studies/{study_id}/sample_lists/{sample_list_id}"
        )


def handle_signal(signum, frame):
    logger.info(f"Signal {signum} received, initiating shutdown...")
    # Note: Actual shutdown logic might need to be coordinated with asyncio loop
    # For simplicity, we'll exit. FastMCP's run might handle this more gracefully.
    sys.exit(0)


def setup_signal_handlers():
    signal.signal(signal.SIGINT, handle_signal)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_signal)  # Handle termination


async def main():
    parser = argparse.ArgumentParser(description="Run the cBioPortal MCP Server.")
    parser.add_argument(
        "--base-url",
        default="https://www.cbioportal.org/api",
        help="Base URL for the cBioPortal API.",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio"],  # Limiting to stdio for now to simplify
        help="Transport protocol for MCP communication (currently only 'stdio' supported).",
    )
    # parser.add_argument(
    #     "--port",
    #     type=int,
    #     default=8000,
    #     help="Port for WebSocket transport (if used)."
    # )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],  # Ensure logs go to stderr
    )
    global logger  # Use global logger after basicConfig is set
    logger = logging.getLogger(__name__)  # Re-assign to get logger with new config

    setup_signal_handlers()  # Setup signal handlers for graceful shutdown

    server_instance = CBioPortalMCPServer(base_url=args.base_url)

    logger.info(f"Starting cBioPortal MCP Server with transport: {args.transport}")

    if args.transport.lower() == "stdio":
        try:
            # Use run_async directly to avoid creating a new event loop
            # This is needed for compatibility with Claude Desktop which already has an event loop
            await server_instance.mcp.run_async(transport="stdio")
        except KeyboardInterrupt:
            logger.info("Server interrupted by user (KeyboardInterrupt).")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during server execution: {e}",
                exc_info=True,
            )
        finally:
            logger.info("Server shutdown sequence initiated from main.")
            # Explicitly call shutdown hooks if not handled by FastMCP
            if server_instance.client is not None:
                await server_instance.shutdown()
            # For now, assuming FastMCP handles it.
    else:
        logger.error(f"Unsupported transport: {args.transport}")
        sys.exit(1)

    logger.info("cBioPortal MCP Server has shut down.")


if __name__ == "__main__":
    asyncio.run(main())

# End of file
