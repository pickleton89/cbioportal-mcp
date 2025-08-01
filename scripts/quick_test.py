#!/usr/bin/env python3
"""
Quick test script to verify the async methods are working correctly.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cbioportal_mcp.server import CBioPortalMCPServer
from cbioportal_mcp.config import Configuration


async def run_test():
    """Run a simple test of the key server methods."""
    # Create a configuration for the server (uses defaults including base URL)
    config = Configuration()
    server = CBioPortalMCPServer(config)

    # Create a mock for the API request
    original_make_api_request = server.api_client.make_api_request

    async def mock_api_request(*args, **kwargs):
        # Return simple mock data
        if args[0] == "cancer-types":
            return [{"cancerTypeId": "type_1", "name": "Cancer Type 1"}]
        elif "samples" in args[0]:
            return [{"sampleId": "sample_1", "patientId": "patient_1"}]
        elif args[0] == "genes":
            return [{"entrezGeneId": 1, "hugoGeneSymbol": "GENE1"}]
        return []

    # Replace the API request with our mock
    server.api_client.make_api_request = mock_api_request

    # Test the methods we fixed
    print("Testing get_cancer_types...")
    result = await server.get_cancer_types(page_number=0, page_size=10)
    print(f"Result: {result}\n")

    print("Testing get_samples_in_study...")
    result = await server.get_samples_in_study(
        study_id="study_1", page_number=0, page_size=10
    )
    print(f"Result: {result}\n")

    print("Testing search_genes...")
    result = await server.search_genes(keyword="GENE", page_number=0, page_size=10)
    print(f"Result: {result}\n")

    # Restore original method
    server.api_client.make_api_request = original_make_api_request

    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(run_test())
