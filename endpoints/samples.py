"""
Samples endpoint module for the cBioPortal MCP server.

Contains all sample-related endpoint methods:
- get_samples_in_study: Get samples for a specific study with pagination
- get_sample_list_id: Get sample list information
"""

from typing import Any, Dict, List, Optional

from api_client import APIClient
from utils.validation import (
    validate_page_params,
    validate_sort_params,
    validate_study_id,
)
from utils.logging import get_logger

logger = get_logger(__name__)


class SamplesEndpoints:
    """Handles all sample-related endpoints for the cBioPortal MCP server."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

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
        validate_study_id(study_id)
        validate_page_params(page_number, page_size, limit)
        validate_sort_params(sort_by, direction)

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

    async def get_sample_list_id(self, study_id: str, sample_list_id: str) -> Dict:
        """
        Get sample list information for a specific study and sample list ID.
        
        Args:
            study_id: The ID of the cancer study
            sample_list_id: The ID of the sample list
            
        Returns:
            Dictionary containing sample list information
        """
        return await self.api_client.make_api_request(
            f"studies/{study_id}/sample_lists/{sample_list_id}"
        )