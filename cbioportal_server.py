#!/usr/bin/env python3
"""
cBioPortal MCP Server (clean implementation)
Provides Model Context Protocol tools for accessing the cBioPortal API with full pagination support.
"""

import argparse
from typing import Any, Dict, List, Optional

import requests
from fastmcp import FastMCP

class CBioPortalMCPServer:
    """
    An MCP server that interfaces with the cBioPortal API using FastMCP.
    """
    def __init__(self, base_url: str = "https://www.cbioportal.org/api"):
        self.base_url = base_url
        self.mcp = FastMCP(
            name="cBioPortal",
            description="Access cancer genomics data from cBioPortal",
            instructions="This server provides tools to access and analyze cancer genomics data from cBioPortal.",
        )
        self._register_tools()

    def _register_tools(self):
        self.mcp.tool()(self.get_cancer_studies)
        self.mcp.tool()(self.get_cancer_types)
        self.mcp.tool()(self.get_study_details)
        self.mcp.tool()(self.get_samples_in_study)
        self.mcp.tool()(self.get_genes)
        self.mcp.tool()(self.search_genes)
        self.mcp.tool()(self.get_mutations_in_gene)
        self.mcp.tool()(self.get_clinical_data)
        self.mcp.tool()(self.get_molecular_profiles)
        self.mcp.tool()(self.search_studies)

    def _make_api_request(self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, json_data: Optional[Any] = None) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, json=json_data, params=params)
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

    def get_cancer_studies(self, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Get a list of cancer studies in cBioPortal with pagination support.
        """
        try:
            api_call_params = {"pageNumber": page_number, "pageSize": page_size, "direction": direction}
            if sort_by:
                api_call_params["sortBy"] = sort_by
            if limit == 0: # Intent to fetch all, use a very large page size for API call
                api_call_params["pageSize"] = 10000000
            # If limit is non-zero, api_call_params["pageSize"] remains the original page_size for the API call.
            
            studies_from_api = self._make_api_request("studies", params=api_call_params)

            # Determine if the API might have more data
            api_might_have_more = len(studies_from_api) == api_call_params["pageSize"]
            # If 'fetch all' was intended and API returned less than max fetch size, then it's definitely the end.
            if api_call_params["pageSize"] == 10000000 and len(studies_from_api) < 10000000:
                api_might_have_more = False

            # Apply server-side limit if specified (after fetching the page from API)
            studies_for_response = studies_from_api
            if limit and limit > 0 and len(studies_from_api) > limit:
                studies_for_response = studies_from_api[:limit]
            
            # total_found in pagination now means number of items in this specific response payload
            total_items_in_response = len(studies_for_response)

            return {
                "studies": studies_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size, # Report original requested page_size to client
                    "total_found": total_items_in_response, 
                    "has_more": api_might_have_more
                }
            }
        except Exception as e:
            return {"error": f"Failed to get cancer studies: {str(e)}"}

    def get_cancer_types(self, page_number: int = 0, page_size: int = 50, sort_by: Optional[str] = None, direction: str = "ASC", limit: Optional[int] = None) -> Dict:
        """
        Get a list of all available cancer types in cBioPortal with pagination support.
        """
        try:
            api_call_params = {"pageNumber": page_number, "pageSize": page_size, "direction": direction}
            if sort_by:
                api_call_params["sortBy"] = sort_by
            if limit == 0:
                api_call_params["pageSize"] = 10000000
            
            types_from_api = self._make_api_request("cancer-types", params=api_call_params)

            api_might_have_more = len(types_from_api) == api_call_params["pageSize"]
            if api_call_params["pageSize"] == 10000000 and len(types_from_api) < 10000000:
                api_might_have_more = False

            types_for_response = types_from_api
            if limit and limit > 0 and len(types_from_api) > limit:
                types_for_response = types_from_api[:limit]
            
            total_items_in_response = len(types_for_response)

            return {
                "cancer_types": types_for_response,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_items_in_response,
                    "has_more": api_might_have_more
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

    # --- Other methods ---

    def get_study_details(self, study_id: str) -> Dict:
        """
        Get detailed information about a specific cancer study.

        Args:
            study_id: The ID of the cancer study (e.g., 'acc_tcga').

        Returns:
            A dictionary containing the study details.
        """
        try:
            study = self._make_api_request(f"studies/{study_id}")
            return {"study": study}
        except Exception as e:
            return {"error": f"Failed to get study details for {study_id}: {str(e)}"}

    def get_genes(self, gene_ids: List[str], gene_id_type: str = "ENTREZ_GENE_ID", projection: str = "SUMMARY") -> Dict:
        """
        Get information about specific genes by their Hugo symbol or Entrez ID using batch endpoint.
        """
        try:
            params = {"geneIdType": gene_id_type, "projection": projection}
            gene_data = self._make_api_request("genes/fetch", method="POST", params=params, json_data=gene_ids)
            return {"genes": gene_data}
        except Exception as e:
            return {"error": "Failed to get gene information: " + str(e)}

    def run(self, transport: str = "stdio"):
        if transport.lower() == "stdio":
            self.mcp.run()
        else:
            raise ValueError(f"Unsupported transport: {transport}. Currently only 'stdio' is supported.")

def main():
    parser = argparse.ArgumentParser(description="cBioPortal MCP Server")
    parser.add_argument("--base-url", type=str, default="https://www.cbioportal.org/api", help="Base URL for the cBioPortal API")
    parser.add_argument("--transport", type=str, default="stdio", choices=["stdio"], help="Transport mechanism for the MCP server (e.g., 'stdio')")
    args = parser.parse_args()
    server = CBioPortalMCPServer(base_url=args.base_url)
    try:
        server.run(transport=args.transport)
    except KeyboardInterrupt:
        print("\nServer stopped by user.", flush=True)
    except Exception as e:
        print("An error occurred during server execution: " + str(e), flush=True)

if __name__ == "__main__":
    main()

# End of file
