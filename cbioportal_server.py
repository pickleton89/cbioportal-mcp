#!/usr/bin/env python3
# cBioPortal MCP Server
# This server provides Model Context Protocol tools for accessing the cBioPortal API

import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests

# Import from the FastMCP module, which is the recommended high-level framework
# Assumes FastMCP is installed and available in the environment
from mcp.server.fastmcp import FastMCP


class CBioPortalMCPServer:
    """
    An MCP server that interfaces with the cBioPortal API using FastMCP.
    """

    def __init__(self, base_url: str = "https://www.cbioportal.org/api"):
        """
        Initialize the server with the cBioPortal API base URL and register tools.

        Args:
            base_url: The base URL for the cBioPortal API
        """
        self.base_url = base_url

        # Initialize FastMCP server with name and description
        self.mcp = FastMCP(
            name="cBioPortal",
            description="Access cancer genomics data from cBioPortal",
            instructions="This server provides tools to access and analyze cancer genomics data from cBioPortal.",
        )

        # Register all tools after self.mcp is initialized
        self._register_tools()

    def _register_tools(self):
        """Register all the tools with the FastMCP instance."""
        # Call self.mcp.tool() on each method to register it as a tool
        self.mcp.tool()(self.get_cancer_studies)
        self.mcp.tool()(self.get_cancer_types)
        self.mcp.tool()(self.get_study_details)
        self.mcp.tool()(self.get_samples_in_study)
        self.mcp.tool()(self.get_genes)
        self.mcp.tool()(self.search_genes)
        self.mcp.tool()(self.get_mutations_in_gene)  # Updated tool
        self.mcp.tool()(self.get_clinical_data)
        self.mcp.tool()(self.get_molecular_profiles)
        self.mcp.tool()(self.search_studies)

    def _make_api_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Make a request to the cBioPortal API.

        Args:
            endpoint: The API endpoint (without leading slash)
            method: HTTP method ('GET' or 'POST')
            params: Optional query parameters for GET requests
            json_data: Optional JSON payload for POST requests

        Returns:
            The JSON response from the API. Can be a list or a dictionary.

        Raises:
            Exception: If the API request fails or the response is not valid JSON.
        """
        url = f"{self.base_url}/{endpoint}"
        # Removed terminal debug prints, will include in tool response if error

        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params)
            elif method.upper() == "POST":
                # cBioPortal API often uses POST with a JSON body for fetching data
                response = requests.post(url, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

            # Check if the response body is empty before attempting to parse JSON
            if not response.text:
                # Depending on the API endpoint, an empty response might be valid (e.g., no data found)
                # Returning an empty list or dictionary is safer than raising an error.
                # We'll return an empty list if the response was likely meant to be a list, else empty dict.
                # A simple check could be if the endpoint name suggests a list (plural).
                if endpoint.endswith("s") or endpoint.endswith(
                    "fetch"
                ):  # Basic heuristic
                    return []
                else:
                    return {}  # Or return None, but empty dict/list is often easier to handle downstream

            return response.json()

        except requests.exceptions.HTTPError as e:
            # More specific error for HTTP issues
            try:
                error_details = e.response.json()
            except json.JSONDecodeError:
                error_details = (
                    e.response.text
                )  # Fallback to raw text if JSON decoding fails
            # Return structured error including API status and details
            return {
                "api_error": f"API HTTP error: {e.response.status_code}",
                "api_details": error_details,
                "requested_url": url,
                "requested_method": method,
                "requested_params": params,
                "requested_json_data": json_data,
            }
        except requests.RequestException as e:
            # Catch other requests library errors (network issues, etc.)
            return {
                "api_error": f"API request failed: {str(e)}",
                "requested_url": url,
                "requested_method": method,
                "requested_params": params,
                "requested_json_data": json_data,
            }
        except json.JSONDecodeError:
            # Handle cases where the response is not valid JSON but wasn't empty
            return {
                "api_error": f"Failed to decode API response as JSON",
                "response_text": response.text,
                "requested_url": url,
                "requested_method": method,
                "requested_params": params,
                "requested_json_data": json_data,
            }
        except Exception as e:
            # Catch any other unexpected errors
            return {
                "api_error": f"An unexpected error occurred during API request: {str(e)}",
                "requested_url": url,
                "requested_method": method,
                "requested_params": params,
                "requested_json_data": json_data,
            }

    def get_cancer_studies(
        self,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None
    ) -> Dict:
        """
        Get a list of cancer studies in cBioPortal with pagination support.
        
        Args:
            page_number: Page number (0-indexed) to retrieve
            page_size: Number of studies per page (default: 50)
            sort_by: Field to sort by. Valid options: "studyId", "name", "description",
                    "publicStudy", "cancerTypeId", "status"
            direction: Sort direction ("ASC" or "DESC")
            limit: Maximum total results to return across all pages
                    Set to None to use pagination, 0 for all results
        
        Returns:
            A dictionary containing:
            - studies: List of study objects
            - pagination: Dictionary with pagination metadata
              - page: Current page number
              - page_size: Items per page
              - total_found: Total number of studies matching criteria (if available)
              - has_more: Boolean indicating if more pages exist
        """
        try:
            # Fetch all studies
            studies = self._make_api_request("studies")

            # Limit the number of studies returned to prevent overwhelming the context
            # A note is added to inform the user that the list is truncated.
            return {
                "count": len(studies),
                "studies": studies[:20],  # Return only the first 20 studies
                "note": "Showing first 20 studies. Use search_studies to find specific studies or request more.",
            }
        except Exception as e:
            # Return an error dictionary if the API call fails
            return {"error": f"Failed to get cancer studies: {str(e)}"}

    def get_cancer_types(
        self,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None
    ) -> Dict:
        """
        Get a list of all available cancer types in cBioPortal with pagination support.

        Args:
            page_number: Page number (0-indexed) to retrieve
            page_size: Number of cancer types per page (default: 50)
            sort_by: Field to sort by. Valid options: "cancerTypeId", "name", "dedicatedColor",
                    "shortName", "parent"
            direction: Sort direction ("ASC" or "DESC")
            limit: Maximum total results to return across all pages
                    Set to None to use pagination, 0 for all results
            
        Returns:
            A dictionary containing:
            - cancer_types: List of cancer type objects
            - pagination: Dictionary with pagination metadata
              - page: Current page number
              - page_size: Items per page
              - total_found: Total number of cancer types matching criteria (if available)
              - has_more: Boolean indicating if more pages exist
        """
        try:
            # Special case for "all results" request
            if limit == 0:
                page_size = 10000000  # API's maximum
                
            params = {
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction
            }
            
            if sort_by:
                params["sortBy"] = sort_by
                
            cancer_types = self._make_api_request("cancer-types", params=params)
            
            # Apply limit if specified
            if limit and limit > 0 and len(cancer_types) > limit:
                cancer_types = cancer_types[:limit]
                
            # Determine if more results are likely available
            has_more = len(cancer_types) == page_size
            
            return {
                "cancer_types": cancer_types,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": None,  # API doesn't provide this
                    "has_more": has_more
                }
            }
        except Exception as e:
            # Return an error dictionary if the API call fails
            return {"error": f"Failed to get cancer types: {str(e)}"}

    def get_study_details(self, study_id: str) -> Dict:
        """
        Get detailed information about a specific cancer study, including associated sample lists.

        Args:
            study_id: The ID of the cancer study (e.g., 'acc_tcga').

        Returns:
            A dictionary containing the study details and its sample lists.
        """
        try:
            # Fetch study details
            study = self._make_api_request(f"studies/{study_id}")

            # Fetch additional information about the study, such as sample lists
            sample_lists = self._make_api_request(f"studies/{study_id}/sample-lists")

            return {"study_details": study, "sample_lists": sample_lists}
        except Exception as e:
            # Return an error dictionary if the API call fails
            return {"error": f"Failed to get study details for {study_id}: {str(e)}"}

    def get_samples_in_study(
        self, 
        study_id: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None
    ) -> Dict:
        """
        Get a list of samples associated with a specific cancer study with pagination support.

        Args:
            study_id: The ID of the cancer study (e.g., 'acc_tcga').
            page_number: Page number (0-indexed) to retrieve
            page_size: Number of samples per page (default: 50)
            sort_by: Field to sort by. Valid options: "sampleId", "sampleType"
            direction: Sort direction ("ASC" or "DESC")
            limit: Maximum total results to return across all pages
                    Set to None to use pagination, 0 for all results
                    
        Returns:
            A dictionary containing:
            - samples: List of sample objects
            - pagination: Dictionary with pagination metadata
              - page: Current page number
              - page_size: Items per page
              - total_found: Total number of samples matching criteria (if available)
              - has_more: Boolean indicating if more pages exist
        """
        try:
            # Special case for "all results" request
            if limit == 0:
                page_size = 10000000  # API's maximum
                
            params = {
                "pageNumber": page_number,
                "pageSize": page_size,
                "direction": direction
            }
            
            if sort_by:
                params["sortBy"] = sort_by
                
            samples = self._make_api_request(f"studies/{study_id}/samples", params=params)
            
            # Apply limit if specified
            if limit and limit > 0 and len(samples) > limit:
                samples = samples[:limit]
                
            # Determine if more results are likely available
            has_more = len(samples) == page_size
            
            return {
                "samples": samples,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": None,  # API doesn't provide this
                    "has_more": has_more
                }
            }
        except Exception as e:
            # Return an error dictionary if the API call fails
            return {"error": f"Failed to get samples for {study_id}: {str(e)}"}

    def get_genes(
        self, 
        gene_ids: List[str],
        gene_id_type: str = "ENTREZ_GENE_ID",
        projection: str = "SUMMARY"
    ) -> Dict:
        """
        Get information about specific genes by their Hugo symbol or Entrez ID.

        Args:
            gene_ids: List of Hugo gene symbols or Entrez gene IDs (e.g., ['BRCA1', 'TP53', '672']).
            gene_id_type: Type of gene ID provided. Options: "ENTREZ_GENE_ID", "HUGO_GENE_SYMBOL"
            projection: Level of detail in the response. Options: "ID", "SUMMARY", "DETAILED", "META"

        Returns:
            A dictionary containing:
            - genes: List of gene objects with information for each requested gene
        """
        results = {}

        try:
            # Iterate through each gene ID and fetch its information
            for gene_id in gene_ids:
                try:
                    # cBioPortal API allows fetching a gene by its ID directly
                    gene_info = self._make_api_request(f"genes/{gene_id}")
                    results[gene_id] = gene_info
                except Exception:
                    # If a specific gene lookup fails, record an error for that gene
                    results[gene_id] = {
                        "error": f"Gene '{gene_id}' not found or lookup failed"
                    }

            return {"genes": results}
        except Exception as e:
            # Return a general error if the overall process fails
            return {"error": f"Failed to get gene information: {str(e)}"}

    def search_genes(
        self, 
        keyword: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None
    ) -> Dict:
        """
        Search for genes by keyword in their symbol or name with pagination support.

        Args:
            keyword: Keyword to search for (e.g., 'BRCA', 'kinase').
            page_number: Page number (0-indexed) to retrieve
            page_size: Number of genes per page (default: 50)
            sort_by: Field to sort by. Valid options: "entrezGeneId", "hugoGeneSymbol", "type", 
                    "cytoband", "length"
            direction: Sort direction ("ASC" or "DESC")
            limit: Maximum total results to return across all pages
                    Set to None to use pagination, 0 for all results

        Returns:
            A dictionary containing:
            - genes: List of gene objects matching the keyword
            - pagination: Dictionary with pagination metadata
              - page: Current page number
              - page_size: Items per page
              - total_found: Total number of genes matching criteria (if available)
              - has_more: Boolean indicating if more pages exist
        """
        try:
            # The cBioPortal API has a search endpoint for genes
            # Using a POST request with the keyword in the body
            payload = {"keyword": keyword}
            matching_genes = self._make_api_request(
                "genes/search", method="POST", json_data=payload
            )

            # The API returns a list of matching genes
            return {"count": len(matching_genes), "matching_genes": matching_genes}
        except Exception as e:
            # Return an error dictionary if the API call fails
            return {"error": f"Failed to search genes for '{keyword}': {str(e)}"}

    # --- UPDATED TOOL: get_mutations_in_gene ---
    def get_mutations_in_gene(
        self, gene_id: str, study_id: str, sample_list_id: str
    ) -> Dict:
        """
        Get mutations in a specific gene for a given study and sample list.
        Uses the /molecular-profiles/{molecularProfileId}/mutations endpoint with GET and query parameters.

        Args:
            gene_id: Hugo gene symbol or Entrez gene ID (e.g., 'BRCA1' or '672').
            study_id: The ID of the cancer study (e.g., 'acc_tcga').
            sample_list_id: The ID of the sample list within the study (e.g., 'acc_tcga_all').

        Returns:
            A dictionary containing the count of mutations and a limited list of mutation details.
        """
        try:
            # First, find the molecular profile ID for mutations in the study
            # This step is necessary because the GET endpoint requires the molecular profile ID in the path.
            molecular_profiles_response = self._make_api_request(
                f"studies/{study_id}/molecular-profiles"
            )

            # Check if fetching molecular profiles resulted in an API error
            if (
                isinstance(molecular_profiles_response, dict)
                and "api_error" in molecular_profiles_response
            ):
                return {
                    "error": f"Failed to fetch molecular profiles for study {study_id}",
                    "details": molecular_profiles_response,
                }

            mutation_profile_id = None
            # Look for the profile with molecularAlterationType "MUTATION_EXTENDED"
            if isinstance(
                molecular_profiles_response, list
            ):  # Ensure response is a list before iterating
                for profile in molecular_profiles_response:
                    if profile.get("molecularAlterationType") == "MUTATION_EXTENDED":
                        mutation_profile_id = profile.get("molecularProfileId")
                        break
            # If it wasn't a list and not an api_error, something else unexpected happened
            elif (
                molecular_profiles_response is not None
                and molecular_profiles_response != {}
            ):
                return {
                    "error": f"Unexpected response format fetching molecular profiles for study {study_id}",
                    "details": molecular_profiles_response,
                }

            if not mutation_profile_id:
                # If no mutation profile is found for the study, return an error
                return {
                    "error": f"No mutation data available (no MUTATION_EXTENDED profile) found for study {study_id}"
                }

            # Use the /molecular-profiles/{molecularProfileId}/mutations endpoint with GET
            # Pass studyId and sampleListId as query parameters.
            endpoint = f"molecular-profiles/{mutation_profile_id}/mutations"
            params = {
                "studyId": study_id,
                "sampleListId": sample_list_id,
            }

            # Add either entrezGeneId or hugoGeneSymbol based on the input gene_id
            if str(
                gene_id
            ).isdigit():  # Ensure gene_id is treated as string for isdigit()
                params["entrezGeneId"] = gene_id
            else:
                params["hugoGeneSymbol"] = gene_id

            # Make the GET request with parameters
            mutations = self._make_api_request(endpoint, method="GET", params=params)

            # The API returns a list of mutations. Check if it's a list before proceeding.
            if not isinstance(mutations, list):
                # If the API returned an error or unexpected format, include request details
                error_response = {
                    "error": "API response for mutations was not a list or contained an API error",
                    "details": mutations,  # This will contain the API error details if _make_api_request returned one
                    "mutation_request_endpoint": endpoint,
                    "mutation_request_params": params,
                    "found_mutation_profile_id": mutation_profile_id,  # Include the found profile ID
                }
                return error_response

            # Limit the number of mutations to avoid overwhelming the context
            # A note is added if the list is truncated.
            if len(mutations) > 50:
                return {
                    "count": len(mutations),
                    "mutations": mutations[:50],  # Return only the first 50 mutations
                    "note": f"Showing only the first 50 mutations for {gene_id} in {study_id} ({sample_list_id}). The full result set is larger.",
                }
            else:
                return {"count": len(mutations), "mutations": mutations}
        except Exception as e:
            # Return an error dictionary if the process fails
            return {
                "error": f"An unexpected error occurred in get_mutations_in_gene: {str(e)}"
            }

    # --- END UPDATED TOOL ---

    def get_clinical_data(
        self, study_id: str, attribute_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Get clinical data for patients in a study. Can fetch specific attributes or all.

        Args:
            study_id: The ID of the cancer study (e.g., 'acc_tcga').
            attribute_ids: Optional list of clinical attribute IDs (e.g., ['CANCER_TYPE', 'AGE']).
                           If None, all available clinical data attributes are returned.

        Returns:
            A dictionary containing the count of clinical data entries and the data,
            grouped by patient ID.
        """
        try:
            clinical_data = []
            if attribute_ids:
                # If specific attribute IDs are provided, use the fetch endpoint with POST
                endpoint = f"studies/{study_id}/clinical-data/fetch"
                payload = {
                    "attributeIds": attribute_ids,
                    "clinicalDataType": "PATIENT",
                }  # Assuming PATIENT level data is requested
                clinical_data = self._make_api_request(
                    endpoint, method="POST", json_data=payload
                )
            else:
                # If no specific attributes are requested, fetch all clinical data using GET
                endpoint = f"studies/{study_id}/clinical-data"
                clinical_data = self._make_api_request(endpoint, method="GET")

            # Group the clinical data by patient ID for easier analysis
            by_patient = {}
            for item in clinical_data:
                patient_id = item.get("patientId")
                if patient_id:  # Only process entries with a valid patient ID
                    if patient_id not in by_patient:
                        by_patient[patient_id] = {}
                    # Store the value under the attribute ID key for each patient
                    by_patient[patient_id][item.get("clinicalAttributeId")] = item.get(
                        "value"
                    )

            return {"count": len(clinical_data), "clinical_data_by_patient": by_patient}
        except Exception as e:
            # Return an error dictionary if the process fails
            return {"error": f"Failed to get clinical data for {study_id}: {str(e)}"}

    def get_molecular_profiles(self, study_id: str) -> Dict:
        """
        Get a list of molecular profiles available for a specific cancer study.

        Args:
            study_id: The ID of the cancer study (e.g., 'acc_tcga').

        Returns:
            A dictionary containing the count of molecular profiles and the list of profiles.
        """
        try:
            # Fetch molecular profiles for the given study ID
            profiles = self._make_api_request(f"studies/{study_id}/molecular-profiles")

            return {"count": len(profiles), "molecular_profiles": profiles}
        except Exception as e:
            # Return an error dictionary if the API call fails
            return {
                "error": f"Failed to get molecular profiles for {study_id}: {str(e)}"
            }

    def search_studies(self, keyword: str) -> Dict:
        """
        Search for cancer studies by keyword in their name or description.
{{ ... }}
        Args:
            keyword: Keyword to search for (e.g., 'melanoma', 'lung cancer').

        Returns:
            A dictionary containing the count of matching studies and a list of study details.
        """
        try:
            # Fetch all studies and filter client-side as the API doesn't have a dedicated
            # search endpoint with keyword filtering parameters on the /studies list itself.
            # This might be inefficient for a very large number of studies.
            all_studies = self._make_api_request("studies")

            # Filter studies where the keyword appears in the name or description (case-insensitive)
            keyword_lower = keyword.lower()
            matching_studies = [
                study
                for study in all_studies
                if keyword_lower in study.get("name", "").lower()
                or keyword_lower in study.get("description", "").lower()
            ]

            return {
                "count": len(matching_studies),
                "matching_studies": matching_studies,
            }
        except Exception as e:
            # Return an error dictionary if the process fails
            return {"error": f"Failed to search studies for '{keyword}': {str(e)}"}

    def run(self, transport: str = "stdio"):
        """
        Run the MCP server with the specified transport mechanism.

        Args:
            transport: The transport mechanism to use ('stdio' is currently the only supported).
        """
        # Removed the print statement that caused the JSON error
        # print(f"Starting cBioPortal MCP server with {transport} transport...", flush=True)

        # The tools are registered in the __init__ method via _register_tools().
        # No need to access them here just for registration purposes.

        # Run the server using the specified transport
        # FastMCP's run() method handles the transport implicitly based on configuration/environment.
        if transport.lower() == "stdio":
            self.mcp.run()
        else:
            # Raise an error for unsupported transports
            raise ValueError(
                f"Unsupported transport: {transport}. Currently only 'stdio' is supported."
            )


def main():
    """Entry point for the cBioPortal MCP server."""
    # Set up argument parsing for base URL and transport
    parser = argparse.ArgumentParser(description="cBioPortal MCP Server")
    parser.add_argument(
        "--base-url",
        type=str,
        default="https://www.cbioportal.org/api",
        help="Base URL for the cBioPortal API",
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio"],  # Restrict choices to currently supported transports
        help="Transport mechanism for the MCP server (e.g., 'stdio')",
    )
    args = parser.parse_args()

    # Create an instance of the server with the provided arguments
    # Tool registration happens within the __init__ method
    server = CBioPortalMCPServer(base_url=args.base_url)

    # Run the server, handling KeyboardInterrupt for graceful shutdown
    try:
        server.run(transport=args.transport)
    except KeyboardInterrupt:
        print("\nServer stopped by user.", flush=True)
    except Exception as e:
        print(f"An error occurred during server execution: {str(e)}", flush=True)


if __name__ == "__main__":
    # Execute the main function when the script is run directly
    main()
