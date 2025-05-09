#!/usr/bin/env python3
# Tests for pagination functionality in the cBioPortal MCP Server

import unittest
from unittest.mock import patch
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
        
        # Call the method with pagination params
        result = self.server.get_cancer_studies(page_number=0, page_size=20)
        
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
        result = self.server.get_cancer_studies(page_number=1, page_size=20)
        
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
        
        # Call with sort parameters
        result = self.server.get_cancer_studies(
            page_number=0, 
            page_size=20, 
            sort_by="name", 
            direction="DESC"
        )
        
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
        
        # Call with limit
        result = self.server.get_cancer_studies(
            page_number=0, 
            page_size=50, 
            limit=30
        )
        
        # Verify limit was applied
        self.assertEqual(len(result["studies"]), 30)

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_cancer_types_pagination(self, mock_api_request):
        """Test pagination for cancer types endpoint."""
        # Set up the mock
        mock_api_request.return_value = self.mock_cancer_types[:10]
        
        # Call the method
        result = self.server.get_cancer_types(page_number=0, page_size=10)
        
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
        
        # Call the method
        result = self.server.get_samples_in_study(
            study_id=study_id,
            page_number=0, 
            page_size=25
        )
        
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
        
        # Call the method
        result = self.server.search_genes(
            keyword=keyword,
            page_number=0, 
            page_size=15
        )
        
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

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_all_results(self, mock_api_request):
        """Test the special case of getting all results."""
        mock_api_request.return_value = self.mock_studies
        
        # Call with limit=0 (all results)
        result = self.server.get_cancer_studies(limit=0)
        
        # Verify that max page size was used
        mock_api_request.assert_called_with("studies", params={
            "pageNumber": 0, 
            "pageSize": 10000000,  # API max
            "direction": "ASC"
        })
        
        # Verify all results were returned
        self.assertEqual(len(result["studies"]), len(self.mock_studies))

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_mutations_in_gene_pagination(self, mock_api_request):
        """Test pagination for get_mutations_in_gene method."""
        gene_id = "TP53"
        study_id = "study_mut"
        sample_list_id = "sample_list_1"
        page_size = 20

        # First page
        mock_api_request.return_value = self.mock_mutations[:page_size]
        result = self.server.get_mutations_in_gene(
            gene_id=gene_id, 
            study_id=study_id, 
            sample_list_id=sample_list_id, 
            page_number=0, 
            page_size=page_size
        )
        expected_endpoint = f"molecular-profiles/{gene_id}_mutation/mutations"
        mock_api_request.assert_called_with(expected_endpoint, params={
            "pageNumber": 0, 
            "pageSize": page_size, 
            "direction": "ASC",
            "studyId": study_id,
            "sampleListId": sample_list_id
        })
        self.assertEqual(len(result["mutations"]), page_size)
        self.assertEqual(result["pagination"]["page"], 0)
        self.assertEqual(result["pagination"]["page_size"], page_size)
        self.assertTrue(result["pagination"]["has_more"])

        # Second page
        mock_api_request.return_value = self.mock_mutations[page_size : page_size * 2]
        result = self.server.get_mutations_in_gene(
            gene_id=gene_id, 
            study_id=study_id, 
            sample_list_id=sample_list_id, 
            page_number=1, 
            page_size=page_size
        )
        mock_api_request.assert_called_with(expected_endpoint, params={
            "pageNumber": 1, 
            "pageSize": page_size, 
            "direction": "ASC",
            "studyId": study_id,
            "sampleListId": sample_list_id
        })
        self.assertEqual(len(result["mutations"]), page_size)
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

        # Mock sorted and limited data
        # Actual sorting happens API side, so mock just returns expected slice
        mock_api_request.return_value = sorted(
            self.mock_mutations, 
            key=lambda m: m[sort_by_field],
            reverse=True
        )[:page_size] # API would return a page
        
        result = self.server.get_mutations_in_gene(
            gene_id=gene_id, 
            study_id=study_id, 
            sample_list_id=sample_list_id, 
            page_number=0, 
            page_size=page_size, 
            sort_by=sort_by_field, 
            direction="DESC",
            limit=limit_val
        )

        expected_endpoint = f"molecular-profiles/{gene_id}_mutation/mutations"
        mock_api_request.assert_called_with(expected_endpoint, params={
            "pageNumber": 0, 
            "pageSize": page_size, 
            "direction": "DESC",
            "sortBy": sort_by_field,
            "studyId": study_id,
            "sampleListId": sample_list_id
        })
        self.assertEqual(len(result["mutations"]), limit_val) # Server-side limit application
        self.assertTrue(all(isinstance(m, dict) for m in result["mutations"]))

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_clinical_data_pagination(self, mock_api_request):
        """Test pagination for get_clinical_data method."""
        study_id = "study_clin"
        page_size = 20
        attribute_ids_to_test = ["AGE_AT_DIAGNOSIS", "SEX"]

        # First page
        mock_api_request.return_value = self.mock_clinical_data[:page_size]
        result = self.server.get_clinical_data(
            study_id=study_id, 
            attribute_ids=attribute_ids_to_test,
            page_number=0, 
            page_size=page_size
        )
        expected_endpoint = f"studies/{study_id}/clinical-data"
        mock_api_request.assert_called_with(expected_endpoint, params={
            "pageNumber": 0, 
            "pageSize": page_size, 
            "direction": "ASC",
            "attributeIds": ",".join(attribute_ids_to_test)
        })
        self.assertEqual(len(result["clinical_data"]), page_size)
        self.assertEqual(result["pagination"]["page"], 0)
        self.assertEqual(result["pagination"]["page_size"], page_size)
        self.assertTrue(result["pagination"]["has_more"])

        # Second page (without attribute_ids for variation)
        mock_api_request.return_value = self.mock_clinical_data[page_size : page_size * 2]
        result = self.server.get_clinical_data(
            study_id=study_id, 
            page_number=1, 
            page_size=page_size
        )
        mock_api_request.assert_called_with(expected_endpoint, params={
            "pageNumber": 1, 
            "pageSize": page_size, 
            "direction": "ASC"
            # attributeIds is not passed here, as per call
        })
        self.assertEqual(len(result["clinical_data"]), page_size)
        self.assertEqual(result["pagination"]["page"], 1)

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_clinical_data_with_sort_and_limit(self, mock_api_request):
        """Test sorting and limit for get_clinical_data."""
        study_id = "study_clin"
        sort_by_field = "value" # Assuming sorting by 'value' of an attribute
        limit_val = 15
        page_size = 30

        # Mock API returning a page of sorted data
        # Actual sorting is API-side
        mock_api_request.return_value = sorted(
            self.mock_clinical_data, 
            key=lambda cd: cd.get(sort_by_field, ""), # a bit simplistic for mixed types
            reverse=False 
        )[:page_size]

        result = self.server.get_clinical_data(
            study_id=study_id, 
            page_number=0, 
            page_size=page_size, 
            sort_by=sort_by_field, 
            direction="ASC",
            limit=limit_val
        )

        expected_endpoint = f"studies/{study_id}/clinical-data"
        mock_api_request.assert_called_with(expected_endpoint, params={
            "pageNumber": 0, 
            "pageSize": page_size, 
            "direction": "ASC",
            "sortBy": sort_by_field
            # attributeIds is not passed here
        })
        self.assertEqual(len(result["clinical_data"]), limit_val) # Server-side limit applied
        self.assertTrue(all(isinstance(cd, dict) for cd in result["clinical_data"]))


if __name__ == '__main__':
    unittest.main()
