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


if __name__ == '__main__':
    unittest.main()
