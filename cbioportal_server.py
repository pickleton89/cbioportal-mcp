#!/usr/bin/env python3
"""
cBioPortal MCP Server (clean implementation)
Provides Model Context Protocol tools for accessing the cBioPortal API with full pagination support.
"""

import argparse
import logging
import signal
import sys
from typing import Any, Dict, List, Optional, AsyncGenerator

import httpx
import asyncio
from fastmcp import FastMCP

class CBioPortalMCPServer:
    """
    An MCP server that interfaces with the cBioPortal API using FastMCP.
    """
    def __init__(self, base_url: str = "https://www.cbioportal.org/api"):
        self.base_url = base_url
        self.client = None  # Will be initialized in startup
        self.mcp = FastMCP(
            name="cBioPortal",
            description="Access cancer genomics data from cBioPortal",
            instructions="This server provides tools to access and analyze cancer genomics data from cBioPortal.",
        )
        # Initialize resources
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Register tools
        self._register_tools()
        
    async def startup(self):
        """Initialize async resources when server starts."""
        self.client = httpx.AsyncClient(timeout=30.0)
        print("cBioPortal MCP Server started with async HTTP client")
        
    async def shutdown(self):
        """Clean up async resources when server shuts down."""
        if self.client:
            await self.client.aclose()
            print("cBioPortal MCP Server async HTTP client closed")
            
    async def paginate_results(self, endpoint: str, params: Dict[str, Any] = None, method: str = "GET", json_data: Any = None, max_pages: int = None) -> AsyncGenerator[List[Dict[str, Any]], None]:
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
            results = await self._make_api_request(
                endpoint, 
                method=method, 
                params=request_params,
                json_data=json_data
            )
            
            # Check if we got any results
            if not results or len(results) == 0:
                break
                
            yield results
            
            # Check if we have more pages
            has_more = len(results) >= page_size
            
            # Increment counters
            page += 1
            page_count += 1
            
    async def collect_all_results(self, endpoint: str, params: Dict[str, Any] = None, method: str = "GET", json_data: Any = None, max_pages: int = None, limit: int = None) -> List[Dict[str, Any]]:
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
        
        async for page in self.paginate_results(endpoint, params, method, json_data, max_pages):
            all_results.extend(page)
            
            # Stop if we've reached the specified limit
            if limit and len(all_results) >= limit:
                all_results = all_results[:limit]
                break
                
        return all_results


    def _register_tools(self):
        """
        Register all methods as MCP tools.
        
        FastMCP automatically detects async methods and handles them correctly.
        When an async method is called through the MCP interface, FastMCP will:
        1. Run the method in the event loop
        2. Await the result
        3. Return the result to the client
        
        This makes the async implementation completely transparent to MCP clients.
        """
        # Data retrieval tools
        self.mcp.tool(description="Get cancer studies with pagination support")(self.get_cancer_studies)
        self.mcp.tool(description="Get cancer types with pagination support")(self.get_cancer_types)
        self.mcp.tool(description="Get detailed information about a specific study")(self.get_study_details)
        self.mcp.tool(description="Get samples in a study with pagination support")(self.get_samples_in_study)
        self.mcp.tool(description="Get information about specific genes")(self.get_genes)
        self.mcp.tool(description="Search for genes by keyword with pagination support")(self.search_genes)
        
        # Molecular data tools
        self.mcp.tool(description="Get mutations in a gene with pagination support")(self.get_mutations_in_gene)
        self.mcp.tool(description="Get clinical data with pagination support")(self.get_clinical_data)
        self.mcp.tool(description="Get molecular profiles with pagination support")(self.get_molecular_profiles)
        self.mcp.tool(description="Search for studies by keyword with pagination support")(self.search_studies)
        
        # Concurrent bulk operations
        self.mcp.tool(description="Get multiple studies concurrently for better performance")(self.get_multiple_studies)
        self.mcp.tool(description="Get multiple genes concurrently with automatic batching")(self.get_multiple_genes)

    async def _make_api_request(self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, json_data: Optional[Any] = None) -> Any:
        """Make an asynchronous API request to the cBioPortal API."""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=json_data, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            response.raise_for_status()
            if not response.text:
                if endpoint.endswith("s") or endpoint.endswith("fetch"):
                    return []
                else:
                    return {}
            return response.json()
        except Exception as e:
            raise Exception(f"API request to {endpoint} failed: {str(e)}")

    # --- Collection-returning methods with pagination ---

    async def get_cancer_studies(self, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Get a list of cancer studies in cBioPortal with pagination support.
        
        Args:
            page_number: Page number to retrieve (0-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            direction: Sort direction (ASC or DESC)
            limit: Maximum number of results to return (0 = all available)
            
        Returns:
            Dictionary with studies and pagination metadata
        """
        try:
            # Configure API parameters
            api_params = {"pageNumber": page_number, "pageSize": page_size, "direction": direction}
            if sort_by:
                api_params["sortBy"] = sort_by
                
            # Special behavior for limit=0 (fetch all results)
            if limit == 0:
                # Use the collect_all_results helper which handles pagination automatically
                studies_from_api = await self.collect_all_results("studies", params=api_params)
                studies_for_response = studies_from_api
                has_more = False  # We fetched everything
            else:
                # Fetch just the requested page
                studies_from_api = await self._make_api_request("studies", params=api_params)
                
                # Apply the limit if specified and smaller than the page results
                studies_for_response = studies_from_api
                if limit and 0 < limit < len(studies_from_api):
                    studies_for_response = studies_from_api[:limit]
                
                # Determine if there might be more data available
                has_more = len(studies_from_api) >= page_size
            
            # Count the actual items we're returning
            total_items = len(studies_for_response)
            
            return {
                "studies": studies_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_items,
                    "has_more": has_more
                }
            }
        except Exception as e:
            return {"error": f"Failed to get cancer studies: {str(e)}"}

    async def get_cancer_types(self, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Get a list of all available cancer types in cBioPortal with pagination support.
        
        Args:
            page_number: Page number (0-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            direction: Sort direction (ASC or DESC)
            limit: Maximum number of results to return (0 = all available)
            
        Returns:
            Dictionary with cancer types and pagination metadata
        """
        try:
            # Configure API parameters
            api_params = {"pageNumber": page_number, "pageSize": page_size, "direction": direction}
            if sort_by:
                api_params["sortBy"] = sort_by
                
            # Special behavior for limit=0 (fetch all results)
            if limit == 0:
                # Use the collect_all_results helper for automatic pagination
                types_from_api = await self.collect_all_results("cancer-types", params=api_params)
                types_for_response = types_from_api
                has_more = False  # We fetched everything
            else:
                # Fetch just the requested page
                types_from_api = await self._make_api_request("cancer-types", params=api_params)
                
                # Apply the limit if specified and smaller than the page results
                types_for_response = types_from_api
                if limit and 0 < limit < len(types_from_api):
                    types_for_response = types_from_api[:limit]
            
                # Determine if there might be more data available
                has_more = len(types_from_api) >= page_size
        
            # Count the actual items we're returning
            total_items = len(types_for_response)
        
            return {
                "cancer_types": types_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_items,
                    "has_more": has_more
                }
            }
        except Exception as e:
            return {"error": f"Failed to get cancer types: {str(e)}"}

    def get_samples_in_study(self, study_id: str, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Get a list of samples associated with a specific cancer study with pagination support.
        """
        try:
            api_call_params = {"pageNumber": page_number, "pageSize": page_size, "direction": direction}
            if sort_by:
                api_call_params["sortBy"] = sort_by
            if limit == 0:
                api_call_params["pageSize"] = 10000000

            samples_from_api = self._make_api_request(f"studies/{study_id}/samples", params=api_call_params)
            
            api_might_have_more = len(samples_from_api) == api_call_params["pageSize"]
            if api_call_params["pageSize"] == 10000000 and len(samples_from_api) < 10000000:
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
                    "has_more": api_might_have_more
                }
            }
        except Exception as e:
            return {"error": f"Failed to get samples for study {study_id}: {str(e)}"}

    def search_genes(self, keyword: str, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Search for genes by keyword in their symbol or name with pagination support.
        """
        try:
            api_call_params = {"keyword": keyword, "pageNumber": page_number, "pageSize": page_size, "direction": direction}
            if sort_by:
                api_call_params["sortBy"] = sort_by
            if limit == 0:
                api_call_params["pageSize"] = 10000000

            genes_from_api = self._make_api_request("genes", params=api_call_params) # Corrected endpoint
            
            # Determine if the API might have more data
            api_might_have_more = len(genes_from_api) == api_call_params["pageSize"]
            # If 'fetch all' was intended and API returned less than max fetch size, then it's definitely the end.
            if api_call_params["pageSize"] == 10000000 and len(genes_from_api) < 10000000:
                api_might_have_more = False

            # Apply server-side limit if specified (after fetching the page from API)
            genes_for_response = genes_from_api
            if limit and limit > 0 and len(genes_from_api) > limit:
                genes_for_response = genes_from_api[:limit]

            # total_found in pagination now means number of items in this specific response payload
            total_items_in_response = len(genes_for_response)

            return {
                "genes": genes_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size, # Report original requested page_size to client
                    "total_found": total_items_in_response,
                    "has_more": api_might_have_more
                }
            }
        except Exception as e:
            return {"error": f"Failed to search genes: {str(e)}"}

    def search_studies(self, keyword: str, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Search for cancer studies by keyword in their name or description with pagination support.
        """
        try:
            if limit == 0:
                page_size = 10000000
            all_studies = self._make_api_request("studies")
            keyword_lower = keyword.lower()
            matching_studies = [
                study for study in all_studies
                if keyword_lower in study.get("name", "").lower() or keyword_lower in study.get("description", "").lower()
            ]
            if sort_by:
                reverse = direction.upper() == "DESC"
                matching_studies.sort(key=lambda s: str(s.get(sort_by, "")), reverse=reverse)
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
                    "page_size": page_size,
                    "total_found": total_count,
                    "has_more": has_more
                }
            }
        except Exception as e:
            return {"error": f"Failed to search studies for '{keyword}': {str(e)}"}

    def get_molecular_profiles(self, study_id: str, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Get a list of molecular profiles available for a specific cancer study with pagination support.
        """
        try:
            if limit == 0:
                page_size = 10000000
            profiles = self._make_api_request(f"studies/{study_id}/molecular-profiles")
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
                    "has_more": has_more
                }
            }
        except Exception as e:
            return {"error": f"Failed to get molecular profiles for {study_id}: {str(e)}"}

    def get_mutations_in_gene(self, gene_id: str, study_id: str, sample_list_id: str, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Get mutations in a specific gene for a given study and sample list, with pagination support.
        Uses the /molecular-profiles/{molecularProfileId}/mutations endpoint with GET and query parameters.
        The molecularProfileId is dynamically determined based on the studyId.
        """
        try:
            molecular_profiles_response = self._make_api_request(f"studies/{study_id}/molecular-profiles")
            if isinstance(molecular_profiles_response, dict) and "api_error" in molecular_profiles_response:
                return {"error": f"Failed to fetch molecular profiles for study {study_id} to find mutation profile", "details": molecular_profiles_response}

            mutation_profile_id = None
            if isinstance(molecular_profiles_response, list):
                for profile in molecular_profiles_response:
                    if profile.get("molecularAlterationType") == "MUTATION_EXTENDED":
                        mutation_profile_id = profile.get("molecularProfileId")
                        break
            
            if not mutation_profile_id:
                return {"error": f"No MUTATION_EXTENDED molecular profile found for study {study_id}"}

            api_call_params = {
                "studyId": study_id,
                "sampleListId": sample_list_id,
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction
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
            mutations_from_api = self._make_api_request(endpoint, method="GET", params=api_call_params)

            if isinstance(mutations_from_api, dict) and "api_error" in mutations_from_api:
                 return {"error": "API error fetching mutations", "details": mutations_from_api, "request_params": api_call_params}
            if not isinstance(mutations_from_api, list):
                return {"error": "Unexpected API response type for mutations (expected list)", "details": mutations_from_api, "request_params": api_call_params}

            api_might_have_more = len(mutations_from_api) == api_call_params["pageSize"]
            if api_call_params["pageSize"] == 10000000 and len(mutations_from_api) < 10000000:
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
                    "has_more": api_might_have_more
                }
            }
        except Exception as e:
            return {"error": f"An unexpected error occurred in get_mutations_in_gene: {str(e)}"}

    def get_clinical_data(self, study_id: str, attribute_ids: Optional[List[str]] = None, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Get clinical data for patients in a study with pagination support. Can fetch specific attributes or all.
        """
        try:
            api_call_params = {
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction,
                "clinicalDataType": "PATIENT" # Assuming PATIENT level data
            }
            if sort_by:
                api_call_params["sortBy"] = sort_by
            if limit == 0:
                api_call_params["pageSize"] = 10000000

            clinical_data_from_api = []
            if attribute_ids:
                endpoint = f"studies/{study_id}/clinical-data/fetch"
                payload = {"attributeIds": attribute_ids, "clinicalDataType": "PATIENT"}
                clinical_data_from_api = self._make_api_request(endpoint, method="POST", json_data=payload, params=api_call_params)
            else:
                endpoint = f"studies/{study_id}/clinical-data"
                clinical_data_from_api = self._make_api_request(endpoint, method="GET", params=api_call_params)

            if isinstance(clinical_data_from_api, dict) and "api_error" in clinical_data_from_api:
                 return {"error": "API error fetching clinical data", "details": clinical_data_from_api, "request_params": api_call_params}
            if not isinstance(clinical_data_from_api, list):
                return {"error": "Unexpected API response type for clinical data (expected list)", "details": clinical_data_from_api, "request_params": api_call_params}

            api_might_have_more = len(clinical_data_from_api) == api_call_params["pageSize"]
            if api_call_params["pageSize"] == 10000000 and len(clinical_data_from_api) < 10000000:
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
                    by_patient[patient_id][item.get("clinicalAttributeId")] = item.get("value")
        
            # Update total_found to be the number of unique patients, not raw data items
            # This makes the count consistent with the actual returned data structure
            total_patients = len(by_patient)
        
            return {
                "clinical_data_by_patient": by_patient, # This contains unique patients with their attributes
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_patients,  # Now using patient count for consistency
                    "has_more": api_might_have_more
                }
            }
        except Exception as e:
            return {"error": f"Failed to get clinical data for study {study_id}: {str(e)}"}

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
            return {"studies": {}, "metadata": {"count": 0, "errors": 0}}
            
        # Create a reusable async function for fetching a single study
        async def fetch_study(study_id):
            try:
                data = await self._make_api_request(f"studies/{study_id}")
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
                "concurrent": True
            }
        }
        
    async def get_multiple_genes(self, gene_ids: List[str], gene_id_type: str = "ENTREZ_GENE_ID", projection: str = "SUMMARY") -> Dict:
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
        if not gene_ids:
            return {"genes": {}, "metadata": {"count": 0, "errors": 0}}
        
        # For large gene lists, break into smaller batches for API compatibility
        batch_size = 100  # cBioPortal API handles batches better than very large requests
        gene_batches = [gene_ids[i:i + batch_size] for i in range(0, len(gene_ids), batch_size)]
        
        async def fetch_gene_batch(batch):
            try:
                params = {"geneIdType": gene_id_type, "projection": projection}
                batch_data = await self._make_api_request("genes/fetch", method="POST", params=params, json_data=batch)
                return {"data": batch_data, "success": True}
            except Exception as e:
                return {"error": str(e), "success": False}
        
        # Create tasks for all batches and run them concurrently
        tasks = [fetch_gene_batch(batch) for batch in gene_batches]
        start_time = asyncio.get_event_loop().time()
        batch_results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
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
        for gene in all_genes:
            gene_id = gene.get("entrezGeneId") or gene.get("hugoGeneSymbol")
            if gene_id:
                genes_dict[str(gene_id)] = gene
        
        return {
            "genes": genes_dict,
            "metadata": {
                "count": len(genes_dict),
                "total_requested": len(gene_ids),
                "errors": error_count,
                "execution_time": round(end_time - start_time, 3),
                "concurrent": True,
                "batches": len(gene_batches)
            }
        }
    
    # --- Other methods ---

    async def get_study_details(self, study_id: str) -> Dict:
        """
        Get detailed information about a specific cancer study.

        Args:
            study_id: The ID of the cancer study (e.g., 'acc_tcga').

        Returns:
            A dictionary containing the study details.
        """
        try:
            study = await self._make_api_request(f"studies/{study_id}")
            return {"study": study}
        except Exception as e:
            return {"error": f"Failed to get study details for {study_id}: {str(e)}"}

    async def get_genes(self, gene_ids: List[str], gene_id_type: str = "ENTREZ_GENE_ID", projection: str = "SUMMARY") -> Dict:
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
            gene_data = await self._make_api_request("genes/fetch", method="POST", params=params, json_data=gene_ids)
            return {"genes": gene_data}
        except Exception as e:
            return {"error": f"Failed to get gene information: {str(e)}"}

    async def run(self, transport: str = "stdio", log_level: str = "INFO"):
        """Run the cBioPortal MCP server with the specified transport.
        
        The FastMCP run method automatically handles the async lifecycle for us,
        including calling our startup and shutdown hooks.
        
        Args:
            transport: Transport mechanism for the server (e.g., 'stdio')
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        # Configure logging
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stderr)
            ]
        )
        
        # Log startup information
        logger = logging.getLogger("cbioportal_mcp")
        logger.info(f"Starting cBioPortal MCP Server with async support (API: {self.base_url})")
        
        if transport.lower() == "stdio":
            # FastMCP will properly handle our async lifecycle
            self.mcp.run()
        else:
            raise ValueError(f"Unsupported transport: {transport}. Currently only 'stdio' is supported.")

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    def handle_signal(sig, frame):
        logging.getLogger("cbioportal_mcp").info(f"Received signal {sig}, shutting down...")
        sys.exit(0)
        
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_signal)  # Handle termination

def main():
    """Entry point for the cBioPortal MCP server.
    
    Parses command line arguments and starts the server.
    FastMCP handles the async event loop setup internally.
    """
    parser = argparse.ArgumentParser(description="cBioPortal MCP Server with Async Support")
    parser.add_argument("--base-url", type=str, default="https://www.cbioportal.org/api", help="Base URL for the cBioPortal API")
    parser.add_argument("--transport", type=str, default="stdio", choices=["stdio"], help="Transport mechanism for the MCP server (e.g., 'stdio')")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    args = parser.parse_args()
    
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Configure logging
    numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    logger = logging.getLogger("cbioportal_mcp")
    logger.info("Initializing cBioPortal MCP Server with async support")
    
    # Create and run the server (FastMCP handles the async event loop)
    server = CBioPortalMCPServer(base_url=args.base_url)
    try:
        server.run(transport=args.transport, log_level=args.log_level)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"An error occurred during server execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

# End of file
