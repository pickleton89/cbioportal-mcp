"""
Samples endpoint module for the cBioPortal MCP server.

Contains all sample-related endpoint methods:
- get_samples_in_study: Get samples for a specific study with pagination
- get_sample_list_id: Get sample list information
"""

from typing import Dict, Optional

from .base import BaseEndpoint, handle_api_errors, validate_paginated_params
from ..utils.validation import (
    validate_study_id,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SamplesEndpoints(BaseEndpoint):
    """Handles all sample-related endpoints for the cBioPortal MCP server."""

    def __init__(self, api_client):
        super().__init__(api_client)

    @handle_api_errors("get samples in study")
    @validate_paginated_params
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
        
        return await self.paginated_request(
            endpoint=f"studies/{study_id}/samples",
            page_number=page_number,
            page_size=page_size,
            sort_by=sort_by,
            direction=direction,
            limit=limit,
            data_key="samples"
        )

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
