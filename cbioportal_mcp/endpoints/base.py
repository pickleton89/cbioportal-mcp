"""
Base endpoint class for the cBioPortal MCP server.

This module provides a base class that contains common functionality
shared across all endpoint classes, including pagination logic,
error handling, and response formatting.
"""

import asyncio
from functools import wraps
from typing import Any, Dict, List, Optional, Union

from ..api_client import APIClient
from ..constants import FETCH_ALL_PAGE_SIZE
from ..utils.logging import get_logger
from ..utils.pagination import collect_all_results
from ..utils.validation import validate_page_params, validate_sort_params

logger = get_logger(__name__)


def handle_api_errors(operation_name: str):
    """
    Decorator to handle common API errors consistently across endpoints.
    
    Args:
        operation_name: Description of the operation being performed
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (ValueError, TypeError) as e:
                # Re-raise validation errors so they can be caught by tests
                raise e
            except Exception as e:
                logger.error(f"Error in {operation_name}: {str(e)}")
                return {"error": f"Failed to {operation_name}: {str(e)}"}
        return wrapper
    return decorator


def validate_paginated_params(func):
    """
    Decorator to validate common pagination parameters.
    
    Automatically validates page_number, page_size, limit, sort_by, and direction
    parameters if they exist in the function signature.
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Extract parameters from positional args based on function signature
        import inspect
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())[1:]  # Skip 'self'
        
        # Build a dictionary of parameter values
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()
        
        page_number = bound_args.arguments.get('page_number', 0)
        page_size = bound_args.arguments.get('page_size', 50)
        limit = bound_args.arguments.get('limit', None)
        sort_by = bound_args.arguments.get('sort_by', None)
        direction = bound_args.arguments.get('direction', 'ASC')
        
        # Validate pagination parameters - let exceptions bubble up
        validate_page_params(page_number, page_size, limit)
        validate_sort_params(sort_by, direction)
        
        return await func(self, *args, **kwargs)
    return wrapper


class BaseEndpoint:
    """
    Base class for all endpoint classes.
    
    Provides common functionality including pagination logic,
    error handling, and response formatting.
    """
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    def build_pagination_params(
        self,
        page_number: int,
        page_size: int,
        sort_by: Optional[str],
        direction: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build standardized pagination parameters for API requests.
        
        Args:
            page_number: Page number to retrieve (0-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            direction: Sort direction (ASC or DESC)
            limit: Maximum number of items to return
            
        Returns:
            Dictionary of API parameters
        """
        params = {
            "pageNumber": page_number,
            "pageSize": page_size,
            "direction": direction,
        }
        
        if sort_by:
            params["sortBy"] = sort_by
            
        if limit == 0:
            params["pageSize"] = FETCH_ALL_PAGE_SIZE
            
        return params
    
    def build_pagination_response(
        self,
        results: List[Dict[str, Any]],
        page_number: int,
        page_size: int,
        has_more: bool,
        data_key: str
    ) -> Dict[str, Any]:
        """
        Build standardized pagination response structure.
        
        Args:
            results: List of result items
            page_number: Current page number
            page_size: Page size used
            has_more: Whether more results are available
            data_key: Key name for the results in the response
            
        Returns:
            Standardized response dictionary
        """
        return {
            data_key: results,
            "pagination": {
                "page": page_number,
                "page_size": page_size,
                "total_found": len(results),
                "has_more": has_more,
            },
        }
    
    def determine_has_more(
        self,
        results: List[Dict[str, Any]],
        api_params: Dict[str, Any]
    ) -> bool:
        """
        Determine if more results are available based on the API response.
        
        Args:
            results: Results returned from the API
            api_params: Parameters used in the API call
            
        Returns:
            True if more results might be available, False otherwise
        """
        api_might_have_more = len(results) == api_params["pageSize"]
        
        # If 'fetch all' was intended and API returned less than max fetch size,
        # then it's definitely the end
        if (api_params["pageSize"] == FETCH_ALL_PAGE_SIZE
            and len(results) < FETCH_ALL_PAGE_SIZE):
            api_might_have_more = False
            
        return api_might_have_more
    
    def apply_limit(
        self,
        results: List[Dict[str, Any]],
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        Apply limit to results if specified.
        
        Args:
            results: List of results to limit
            limit: Maximum number of results to return
            
        Returns:
            Limited results list
        """
        if limit and limit > 0 and len(results) > limit:
            return results[:limit]
        return results
    
    async def paginated_request(
        self,
        endpoint: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
        data_key: str = "results",
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a paginated API request with standardized handling.
        
        Args:
            endpoint: API endpoint to call
            page_number: Page number to retrieve (0-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            direction: Sort direction (ASC or DESC)
            limit: Maximum number of items to return
            data_key: Key name for results in response
            additional_params: Additional parameters to include in the request
            
        Returns:
            Standardized paginated response
        """
        # Build base pagination parameters
        api_params = self.build_pagination_params(
            page_number, page_size, sort_by, direction, limit
        )
        
        # Add any additional parameters
        if additional_params:
            api_params.update(additional_params)
        
        # Special behavior for limit=0 (fetch all results)
        if limit == 0:
            results_from_api = await collect_all_results(
                self.api_client, endpoint, params=api_params
            )
            results_for_response = results_from_api
            has_more = False  # We fetched everything
        else:
            # Fetch just the requested page
            results_from_api = await self.api_client.make_api_request(
                endpoint, params=api_params
            )
            
            # Apply limit if specified
            results_for_response = self.apply_limit(results_from_api, limit)
            
            # Determine if there might be more data available
            has_more = self.determine_has_more(results_from_api, api_params)
        
        return self.build_pagination_response(
            results_for_response, page_number, page_size, has_more, data_key
        )
    
    async def concurrent_fetch(
        self,
        fetch_tasks: List[asyncio.Task],
        operation_name: str = "concurrent operation"
    ) -> Dict[str, Any]:
        """
        Execute multiple API requests concurrently and return structured results.
        
        Args:
            fetch_tasks: List of async tasks to execute
            operation_name: Description of the operation for logging
            
        Returns:
            Dictionary with results and metadata
        """
        import time
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*fetch_tasks)
        end_time = time.perf_counter()
        
        # Process results
        success_count = sum(1 for r in results if r.get("success", True))
        error_count = len(results) - success_count
        
        return {
            "results": results,
            "metadata": {
                "count": len(results),
                "errors": error_count,
                "execution_time": round(end_time - start_time, 3),
                "concurrent": True,
                "operation": operation_name,
            },
        }