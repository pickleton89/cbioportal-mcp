#!/usr/bin/env python3
"""
Test script for the async implementation of the cBioPortal MCP server.
This script demonstrates the performance benefits of async operations.
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cbioportal_server import CBioPortalMCPServer


async def test_sequential_vs_concurrent():
    """Compare sequential vs concurrent fetching of multiple studies."""
    print("\n====== Testing Sequential vs Concurrent Performance ======")

    # Initialize the server
    server = CBioPortalMCPServer()

    # Sample study IDs from cBioPortal
    study_ids = [
        "acc_tcga",
        "blca_tcga",
        "brca_tcga",
        "cesc_tcga",
        "chol_tcga",
        "coadread_tcga",
        "dlbc_tcga",
        "esca_tcga",
        "gbm_tcga",
        "hnsc_tcga",
    ]

    print(f"Fetching {len(study_ids)} studies...")

    # Test 1: Sequential fetching
    print("\n--- Sequential Fetching ---")
    start_time = time.time()

    sequential_results = {}
    for study_id in study_ids:
        result = await server.get_study_details(study_id)
        if "study" in result:
            sequential_results[study_id] = result["study"]

    sequential_time = time.time() - start_time
    print(f"Sequential fetching took {sequential_time:.2f} seconds")
    print(f"Retrieved {len(sequential_results)} studies")

    # Test 2: Concurrent fetching
    print("\n--- Concurrent Fetching ---")
    start_time = time.time()

    concurrent_result = await server.get_multiple_studies(study_ids)

    concurrent_time = time.time() - start_time
    print(f"Concurrent fetching took {concurrent_time:.2f} seconds")
    print(f"Retrieved {len(concurrent_result['studies'])} studies")

    # Performance comparison
    speedup = sequential_time / concurrent_time if concurrent_time > 0 else float("inf")
    print(f"\nPerformance improvement: {speedup:.2f}x faster with concurrency")

    # Verify data consistency
    print("\n--- Data Consistency Check ---")
    all_consistent = True
    for study_id in study_ids:
        if study_id in sequential_results and study_id in concurrent_result["studies"]:
            seq_name = sequential_results[study_id].get("name", "")
            conc_name = concurrent_result["studies"][study_id].get("name", "")
            if seq_name != conc_name:
                print(f"Inconsistency found for {study_id}!")
                all_consistent = False

    if all_consistent:
        print("All data is consistent between sequential and concurrent fetching.")

    # Print execution metadata from concurrent operation
    print("\n--- Execution Metadata ---")
    if "metadata" in concurrent_result:
        for key, value in concurrent_result["metadata"].items():
            print(f"{key}: {value}")


async def test_gene_batch_concurrency():
    """Test the concurrent gene batching functionality."""
    print("\n====== Testing Gene Batch Concurrency ======")

    # Initialize the server
    server = CBioPortalMCPServer()

    # Sample gene IDs (mix of Entrez IDs and Hugo symbols)
    gene_ids = [
        "TP53",
        "KRAS",
        "BRCA1",
        "BRCA2",
        "EGFR",
        "PTEN",
        "RB1",
        "AKT1",
        "PIK3CA",
        "VEGFA",
        "MYC",
        "ERBB2",
        "CDK4",
        "CDKN2A",
    ]

    print(f"Fetching {len(gene_ids)} genes with automatic batching...")

    start_time = time.time()
    result = await server.get_multiple_genes(gene_ids, gene_id_type="HUGO_GENE_SYMBOL")
    total_time = time.time() - start_time

    print(f"Fetched {len(result['genes'])} genes in {total_time:.2f} seconds")

    # Print execution metadata
    print("\n--- Execution Metadata ---")
    if "metadata" in result:
        for key, value in result["metadata"].items():
            print(f"{key}: {value}")

    # Print some sample gene data
    print("\n--- Sample Gene Data ---")
    for gene_id, gene_data in list(result["genes"].items())[:3]:  # Just show first 3
        print(
            f"{gene_id}: {gene_data.get('hugoGeneSymbol')} (Entrez ID: {gene_data.get('entrezGeneId')})"
        )


async def main():
    """Run all tests."""
    print("Starting cBioPortal MCP Server Async Tests")
    print("==========================================")

    try:
        # Run the tests
        await test_sequential_vs_concurrent()
        await test_gene_batch_concurrency()

        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Run the async tests
    asyncio.run(main())
