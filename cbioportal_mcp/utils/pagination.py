"""
Pagination utilities for the cBioPortal MCP server.

This module provides reusable pagination functionality for API endpoints.
"""

from typing import Any, Dict, List, Optional, AsyncGenerator


async def paginate_results(
    api_client,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    method: str = "GET",
    json_data: Any = None,
    max_pages: Optional[int] = None,
) -> AsyncGenerator[List[Dict[str, Any]], None]:
    """
    Asynchronous generator that yields pages of results from paginated API endpoints.

    Args:
        api_client: The APIClient instance to use for requests
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
        results = await api_client.make_api_request(
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
    api_client,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    method: str = "GET",
    json_data: Any = None,
    max_pages: Optional[int] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Collect all results from a paginated endpoint into a single list.

    Args:
        api_client: The APIClient instance to use for requests
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

    async for page in paginate_results(
        api_client, endpoint, params, method, json_data, max_pages
    ):
        all_results.extend(page)

        # Stop if we've reached the specified limit
        if limit and len(all_results) >= limit:
            all_results = all_results[:limit]
            break

    return all_results
