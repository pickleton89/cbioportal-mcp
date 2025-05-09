#!/usr/bin/env python3
# Tests for basic functionality of the cBioPortal MCP Server

import unittest
from unittest.mock import patch
import sys
import os

# Add the parent directory to the path so we can import the cbioportal_server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cbioportal_server import CBioPortalMCPServer


class TestCBioPortalServer(unittest.TestCase):
    """Test cases for the cBioPortal MCP Server."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.server = CBioPortalMCPServer(base_url="https://www.cbioportal.org/api")
        
        # Sample mock data for different endpoints
        self.mock_study = {
            "studyId": "study_1",
            "name": "Test Study",
            "description": "A study for testing",
            "publicStudy": True,
            "cancerTypeId": "mixed"
        }
        
        self.mock_gene = {
            "entrezGeneId": 672,
            "hugoGeneSymbol": "BRCA1",
            "type": "protein-coding"
        }

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_study_details(self, mock_api_request):
        """Test that study details retrieval works correctly."""
        # Configure the mock
        study_id = "study_1"
        mock_api_request.return_value = self.mock_study
        
        # Call the method
        result = self.server.get_study_details(study_id)
        
        # Assert the API was called correctly
        mock_api_request.assert_called_once_with(f"studies/{study_id}")
        
        # Assert the result structure
        self.assertEqual(result["study"], self.mock_study)

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_get_genes(self, mock_api_request):
        """Test gene retrieval works correctly."""
        # Configure the mock
        gene_ids = ["BRCA1", "672"]
        mock_api_request.return_value = [self.mock_gene]
        
        # Call the method
        result = self.server.get_genes(
            gene_ids=gene_ids,
            gene_id_type="HUGO_GENE_SYMBOL",
            projection="SUMMARY"
        )
        
        # Assert the API was called correctly
        mock_api_request.assert_called_once_with(
            "genes/fetch", 
            method="POST",
            params={
                "geneIdType": "HUGO_GENE_SYMBOL",
                "projection": "SUMMARY"
            },
            json_data=gene_ids
        )
        
        # Assert the result
        self.assertEqual(result["genes"], [self.mock_gene])

    @patch('cbioportal_server.CBioPortalMCPServer._make_api_request')
    def test_error_handling(self, mock_api_request):
        """Test error handling in the API calls."""
        # Configure the mock to raise an exception
        mock_api_request.side_effect = Exception("API is unavailable")
        
        # Call a method that should handle this error
        result = self.server.get_cancer_studies()
        
        # Assert that the error was handled correctly
        self.assertIn("error", result)
        self.assertIn("Failed to get cancer studies", result["error"])
        self.assertIn("API is unavailable", result["error"])

    def test_api_url_configuration(self):
        """Test that the API URL is configured correctly."""
        # Default URL
        server = CBioPortalMCPServer()
        self.assertEqual(server.base_url, "https://www.cbioportal.org/api")
        
        # Custom URL
        custom_url = "https://custom-cbioportal.example.org/api"
        server = CBioPortalMCPServer(base_url=custom_url)
        self.assertEqual(server.base_url, custom_url)
        

if __name__ == '__main__':
    unittest.main()
