"""
Genes endpoint module for the cBioPortal MCP server.

Contains all gene-related endpoint methods:
- search_genes: Search genes by keyword with pagination
- get_genes: Get gene information using batch endpoint  
- get_multiple_genes: Fetch multiple genes concurrently
- get_mutations_in_gene: Get mutations in a specific gene
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from api_client import APIClient
from utils.validation import (
    validate_page_params,
    validate_sort_params,
    validate_keyword,
    validate_gene_ids_list,
    validate_gene_id_type,
    validate_projection,
)
from utils.logging import get_logger

logger = get_logger(__name__)


class GenesEndpoints:
    """Handles all gene-related endpoints for the cBioPortal MCP server."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

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
        validate_keyword(keyword)
        validate_page_params(page_number, page_size, limit)
        validate_sort_params(sort_by, direction)

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
            )

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