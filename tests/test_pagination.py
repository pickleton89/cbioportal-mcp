#!/usr/bin/env python3
# Tests for pagination functionality in the cBioPortal MCP Server
import unittest
import asyncio
from unittest.mock import patch, call
import sys
import os

# Add the parent directory to the path so we can import the cbioportal_server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cbioportal_server import CBioPortalMCPServer


class TestPagination(unittest.TestCase):
    """Test cases for pagination functionality in the cBioPortal MCP Server."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.server = CBioPortalMCPServer(base_url="https://www.cbioportal.org/api")
        # Create mock data for testing
        self.mock_studies = [
            {"studyId": f"study_{i}", "name": f"Study {i}", "description": f"Description {i}"} 
            for i in range(1, 101)
        ]
        self.mock_cancer_types = [
            {"cancerTypeId": f"type_{i}", "name": f"Cancer Type {i}"} 
            for i in range(1, 51)
        ]
        self.mock_samples = [
            {"sampleId": f"sample_{i}", "patientId": f"patient_{i % 20}", "studyId": "study_1"} 
            for i in range(1, 201)
        ]
        self.mock_genes = [
            {"entrezGeneId": i, "hugoGeneSymbol": f"GENE{i}", "type": "protein-coding"} 
            for i in range(1, 31)
        ]
        self.mock_mutations = [
            {
                "uniqueSampleKey": f"sample_{i}:study_mut",
                "uniquePatientKey": f"patient_{i%20}:study_mut",
                "molecularProfileId": "mutation_profile_1",
                "sampleId": f"sample_{i}",
                "patientId": f"patient_{i%20}",
                "studyId": "study_mut",
                "gene": {"hugoGeneSymbol": "TP53", "entrezGeneId": 7157, "ncbiBuild": "37"},
                "chromosome": "17",
                "startPosition": 7577098 + i,
                "endPosition": 7577098 + i,
                "proteinChange": f"R{175+i}H",
                "mutationStatus": "SOMATIC",
                "mutationType": "Missense_Mutation",
                "keyword": f"TP53_MUT_{i}" # Example field for sorting
            } for i in range(1, 76) # 75 mock mutations
        ]
        self.mock_clinical_data = [
            {
                "uniqueSampleKey": f"sample_{i}:study_clin",
                "uniquePatientKey": f"patient_{i // 2}:study_clin",
                "sampleId": f"sample_{i}",
                "patientId": f"patient_{i // 2}",
                "studyId": "study_clin",
                "attributeId": "AGE_AT_DIAGNOSIS",
                "value": str(40 + i) 
            } for i in range(1, 81) # 80 mock clinical data entries
        ]
        # Add some SEX data for testing attribute_ids variety
        for idx in range(0, len(self.mock_clinical_data)):
            if idx % 3 == 0:
                self.mock_clinical_data[idx]["attributeId"] = "SEX"
                self.mock_clinical_data[idx]["value"] = "Female" if idx % 2 == 0 else "Male"

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_cancer_studies_pagination(self, mock_api_request):
        """Test that the get_cancer_studies method handles pagination correctly."""
        # Configure the mock to return a slice of our mock data
        mock_api_request.return_value = self.mock_studies[:20]
        
        # Call the method with pagination params and run it through the event loop
        result = asyncio.run(self.server.get_cancer_studies(page_number=0, page_size=20))
        
        # Assert that the API was called with the correct parameters
        mock_api_request.assert_called_with("studies", params={
            "pageNumber": 0, 
            "pageSize": 20, 
            "direction": "ASC"
        })
        
        # Assert the structure of the result
        self.assertEqual(len(result["studies"]), 20)
        self.assertEqual(result["pagination"]["page"], 0)
        self.assertEqual(result["pagination"]["page_size"], 20)
        self.assertTrue(result["pagination"]["has_more"])
        
        # Test the next page
        mock_api_request.return_value = self.mock_studies[20:40]
        result = asyncio.run(self.server.get_cancer_studies(page_number=1, page_size=20))
        
        # Assert that the API was called with the correct parameters
        mock_api_request.assert_called_with("studies", params={
            "pageNumber": 1, 
            "pageSize": 20, 
            "direction": "ASC"
        })
        
        # Assert the structure of the result
        self.assertEqual(len(result["studies"]), 20)
        self.assertEqual(result["pagination"]["page"], 1)

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_cancer_studies_with_sort(self, mock_api_request):
        """Test that sorting parameters are correctly passed to the API."""
        mock_api_request.return_value = sorted(
            self.mock_studies[:20], 
            key=lambda s: s["name"], 
            reverse=True
        )
        
        # Call with sort parameters and run it through the event loop
        result = asyncio.run(self.server.get_cancer_studies(
            page_number=0, 
            page_size=20, 
            sort_by="name", 
            direction="DESC"
        ))
        
        # Assert sorting parameters were passed
        mock_api_request.assert_called_with("studies", params={
            "pageNumber": 0, 
            "pageSize": 20,
            "sortBy": "name",
            "direction": "DESC"
        })

        # Verify result structure
        self.assertIsNotNone(result)

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_cancer_studies_limit(self, mock_api_request):
        """Test that the limit parameter works correctly."""
        mock_api_request.return_value = self.mock_studies[:50]
        
        # Call with limit and run it through the event loop
        result = asyncio.run(self.server.get_cancer_studies(
            page_number=0, 
            page_size=50, 
            limit=30
        ))
        
        # Verify limit was applied
        self.assertEqual(len(result["studies"]), 30)

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_cancer_types_pagination(self, mock_api_request):
        """Test pagination for cancer types endpoint."""
        # Set up the mock
        mock_api_request.return_value = self.mock_cancer_types[:10]
        
        # Call the method and run it through the event loop
        result = asyncio.run(self.server.get_cancer_types(page_number=0, page_size=10))
        
        # Verify API call
        mock_api_request.assert_called_with("cancer-types", params={
            "pageNumber": 0, 
            "pageSize": 10, 
            "direction": "ASC"
        })
        
        # Verify result structure
        self.assertEqual(len(result["cancer_types"]), 10)
        self.assertEqual(result["pagination"]["page"], 0)
        self.assertEqual(result["pagination"]["page_size"], 10)
        self.assertTrue(result["pagination"]["has_more"])
        
    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_samples_in_study_pagination(self, mock_api_request):
        """Test pagination for samples in study endpoint."""
        # Set up the mock
        mock_api_request.return_value = self.mock_samples[:25]
        study_id = "study_1"
        
        # Call the method and run it through the event loop
        result = asyncio.run(self.server.get_samples_in_study(
            study_id=study_id,
            page_number=0, 
            page_size=25
        ))
        
        # Verify API call
        mock_api_request.assert_called_with(f"studies/{study_id}/samples", params={
            "pageNumber": 0, 
            "pageSize": 25, 
            "direction": "ASC"
        })
        
        # Verify result structure
        self.assertEqual(len(result["samples"]), 25)
        self.assertEqual(result["pagination"]["page"], 0)
        self.assertEqual(result["pagination"]["page_size"], 25)
        self.assertTrue(result["pagination"]["has_more"])

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_search_genes_pagination(self, mock_api_request):
        """Test pagination for gene search endpoint."""
        # Filter mock data for keyword
        keyword = "GENE"
        matching_genes = [g for g in self.mock_genes if keyword in g["hugoGeneSymbol"]]
        mock_api_request.return_value = matching_genes[:15]
        
        # Call the method and run it through the event loop
        result = asyncio.run(self.server.search_genes(
            keyword=keyword,
            page_number=0, 
            page_size=15
        ))
        
        # Verify API call
        mock_api_request.assert_called_with("genes", params={
            "keyword": keyword,
            "pageNumber": 0, 
            "pageSize": 15, 
            "direction": "ASC"
        })
        
        # Verify result structure
        self.assertEqual(len(result["genes"]), 15)
        self.assertEqual(result["pagination"]["page"], 0)
        self.assertEqual(result["pagination"]["page_size"], 15)
        self.assertTrue(result["pagination"]["has_more"])

    @patch('cbioportal_server.CBioPortalMCPServer.collect_all_results')
    def test_get_all_results(self, mock_collect_all):
        """Test the special case of getting all results."""
        # Set up the mock to return our mock studies directly, bypassing the async iterator
        async def mock_collect_side_effect(*args, **kwargs):
            return self.mock_studies
            
        mock_collect_all.side_effect = mock_collect_side_effect
        
        # Call with limit=0 (all results) and run it through the event loop
        result = asyncio.run(self.server.get_cancer_studies(limit=0))
        
        # Verify collect_all_results was called correctly
        mock_collect_all.assert_called_once()
        
        # Verify all results were returned
        self.assertEqual(len(result["studies"]), len(self.mock_studies))

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_mutations_in_gene_pagination(self, mock_api_request):
        """Test pagination for get_mutations_in_gene method."""
        gene_id = "TP53"
        study_id = "study_mut"
        sample_list_id = "sample_list_1"
        page_size = 25
        
        # For async side effects, we need to use coroutine side_effect values
        async def async_side_effect(*args, **kwargs):
            if args[0] == f"studies/{study_id}/molecular-profiles":
                return [{'molecularProfileId': 'TP53_mutation', 'molecularAlterationType': 'MUTATION_EXTENDED'}]
            else:
                return self.mock_mutations[:25]
                
        mock_api_request.side_effect = async_side_effect
        
        # Call the method and run it through the event loop
        result = asyncio.run(self.server.get_mutations_in_gene(
            gene_id=gene_id,
            study_id=study_id,
            sample_list_id=sample_list_id,
            page_number=0,
            page_size=25
        ))
        
        # Verify API calls - should make two calls
        expected_calls = [
            call(f"studies/{study_id}/molecular-profiles"),
            call(
                "molecular-profiles/TP53_mutation/mutations",
                method="GET",
                params={
                    "studyId": study_id,
                    "sampleListId": sample_list_id,
                    "pageNumber": 0,
                    "pageSize": 25,
                    "direction": "ASC",
                    "hugoGeneSymbol": gene_id
                }
            )
        ]
        mock_api_request.assert_has_calls(expected_calls)
        
        # Verify response structure and pagination
        self.assertEqual(len(result["mutations"]), 25)
        self.assertEqual(result["pagination"]["page"], 0)
        self.assertEqual(result["pagination"]["page_size"], 25)
        self.assertEqual(result["pagination"]["total_found"], 25)
        self.assertEqual(result["mutations"][0]["gene"]["hugoGeneSymbol"], gene_id)
        self.assertTrue(result["pagination"]["has_more"])
        
        # Test second page to ensure pagination is working
        mock_api_request.reset_mock()
        # Set up a new side effect for the second page
        async def second_page_side_effect(*args, **kwargs):
            if args[0] == "studies/" + study_id + "/molecular-profiles":
                return [{"molecularProfileId": "TP53_mutation", "molecularAlterationType": "MUTATION_EXTENDED"}]
            else:
                return self.mock_mutations[page_size:page_size*2]
                
        mock_api_request.side_effect = second_page_side_effect
        
        result = asyncio.run(self.server.get_mutations_in_gene(
            gene_id=gene_id,
            study_id=study_id,
            sample_list_id=sample_list_id,
            page_number=1,
            page_size=page_size
        ))
        
        # Verify second page calls
        expected_calls = [
            call(f"studies/{study_id}/molecular-profiles"),  # First call to get molecular profiles
            call(f"molecular-profiles/{gene_id}_mutation/mutations", method="GET", params={
                "pageNumber": 1,
                "pageSize": page_size,
                "direction": "ASC",
                "studyId": study_id,
                "sampleListId": sample_list_id,
                "hugoGeneSymbol": gene_id
            })  # Second call to get mutations for page 1
        ]
        mock_api_request.assert_has_calls(expected_calls)
        
        # Verify second page pagination details
        self.assertEqual(result["pagination"]["page"], 1)

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_mutations_in_gene_with_sort_and_limit(self, mock_api_request):
        """Test sorting and limit for get_mutations_in_gene."""
        gene_id = "TP53"
        study_id = "study_mut"
        sample_list_id = "sample_list_1"
        sort_by_field = "proteinChange"
        limit_val = 10
        page_size = 25
    
        # Setup mock for async calls properly
        sorted_mutations = sorted(
            self.mock_mutations,
            key=lambda m: m[sort_by_field],
            reverse=True
        )[:page_size]  # API would return a page
        
        # Use an async function for side_effect to handle async method calls
        async def mock_side_effect(*args, **kwargs):
            if args[0] == f"studies/{study_id}/molecular-profiles":
                return [{"molecularProfileId": "TP53_mutation", "molecularAlterationType": "MUTATION_EXTENDED"}]
            else:
                return sorted_mutations
                
        mock_api_request.side_effect = mock_side_effect
    
        result = asyncio.run(self.server.get_mutations_in_gene(
            gene_id=gene_id,
            study_id=study_id,
            sample_list_id=sample_list_id,
            page_number=0,
            page_size=page_size,
            sort_by=sort_by_field,
            direction="DESC",
            limit=limit_val
        ))
    
        # Verify both calls
        expected_calls = [
            call(f"studies/{study_id}/molecular-profiles"),  # First call to get molecular profiles
            call(f"molecular-profiles/{gene_id}_mutation/mutations", method="GET", params={
                "pageNumber": 0,
                "pageSize": page_size,
                "direction": "DESC",
                "sortBy": sort_by_field,
                "studyId": study_id,
                "sampleListId": sample_list_id,
                "hugoGeneSymbol": gene_id
            })  # Second call to get mutations with sort
        ]
        mock_api_request.assert_has_calls(expected_calls)
        
        # Verify limit works - should only be 10 results even though API returned more
        self.assertEqual(len(result["mutations"]), limit_val)
        self.assertEqual(result["pagination"]["total_found"], limit_val)
        self.assertTrue(all(isinstance(m, dict) for m in result["mutations"]))

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_clinical_data_pagination(self, mock_api_request):
        """Test pagination for get_clinical_data method."""
        study_id = "study_clin"
        page_size = 20
    
        # Setup mock for GET request (no attribute_ids)
        mock_api_request.return_value = self.mock_clinical_data[:page_size]
    
        # First page with no attribute_ids (uses GET)
        result = asyncio.run(self.server.get_clinical_data(
            study_id=study_id,
            page_number=0,
            page_size=page_size
        ))
        
        # Verify correct endpoint and params for GET request
        expected_endpoint = f"studies/{study_id}/clinical-data"
        mock_api_request.assert_called_with(expected_endpoint, method="GET", params={
            "pageNumber": 0,
            "pageSize": page_size,
            "direction": "ASC",
            "clinicalDataType": "PATIENT"
        })
        
        # Verify response structure and pagination
        # Note: The clinical_data_by_patient count will be less than page_size
        # because multiple data entries for the same patient are combined
        self.assertTrue(0 < len(result["clinical_data_by_patient"]) <= page_size)
        self.assertEqual(result["pagination"]["page"], 0)
        self.assertEqual(result["pagination"]["page_size"], page_size)
        # total_found now correctly reflects the number of items in the response
        self.assertEqual(result["pagination"]["total_found"], len(result["clinical_data_by_patient"]))
        self.assertTrue(result["pagination"]["has_more"])

        # Second page with no attribute_ids (uses GET)
        mock_api_request.return_value = self.mock_clinical_data[page_size:page_size*2]
        result = asyncio.run(self.server.get_clinical_data(
            study_id=study_id,
            page_number=1,
            page_size=page_size
        ))
        
        # Verify correct endpoint and params for second page GET request
        mock_api_request.assert_called_with(expected_endpoint, method="GET", params={
            "pageNumber": 1,
            "pageSize": page_size,
            "direction": "ASC",
            "clinicalDataType": "PATIENT"
        })
        
        # Verify pagination details for second page
        self.assertEqual(result["pagination"]["page"], 1)

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_clinical_data_with_sort_and_limit(self, mock_api_request):
        """Test sorting and limit for get_clinical_data."""
        study_id = "study_clin"
        sort_by_field = "patientId"
        limit_val = 10
        page_size = 25
        attribute_ids = ["GENDER", "AGE"]
    
        # Mock sorted and limited data for attribute_ids - for the POST request
        mock_api_request.return_value = sorted(
            self.mock_clinical_data,
            key=lambda c: c[sort_by_field],
            reverse=True
        )[:page_size] # API would return a page
    
        result = asyncio.run(self.server.get_clinical_data(
            study_id=study_id,
            attribute_ids=attribute_ids,
            page_number=0,
            page_size=page_size,
            sort_by=sort_by_field,
            direction="DESC",
            limit=limit_val
        ))
    
        # When attribute_ids is provided, it uses a POST request with JSON data
        expected_endpoint = f"studies/{study_id}/clinical-data/fetch"
        expected_payload = {"attributeIds": attribute_ids, "clinicalDataType": "PATIENT"}
        
        mock_api_request.assert_called_with(
            expected_endpoint, 
            method="POST",
            json_data=expected_payload,
            params={
                "pageNumber": 0,
                "pageSize": page_size,
                "direction": "DESC",
                "sortBy": sort_by_field,
                "clinicalDataType": "PATIENT"
            }
        )
        
        # Verify limit works
        # Due to multiple entries per patient being combined, the actual count
        # might be less than the requested limit
        actual_count = len(result["clinical_data_by_patient"])
        self.assertTrue(0 < actual_count <= limit_val, 
                      f"Expected patient count to be between 1 and {limit_val}, got {actual_count}")
        # total_found should match the number of patients
        self.assertEqual(result["pagination"]["total_found"], actual_count)
        # Check that all values in clinical_data_by_patient are dictionaries
        self.assertTrue(all(isinstance(patient_data, dict) for patient_data in result["clinical_data_by_patient"].values()))


if __name__ == '__main__':
    unittest.main()
