#!/usr/bin/env python3
"""
cBioPortal MCP Server (clean implementation)
Provides Model Context Protocol tools for accessing the cBioPortal API with full pagination support.
"""

import argparse
import asyncio
import logging
import signal
import sys
from typing import Any, Dict, List, Optional, AsyncGenerator

import httpx
from fastmcp import FastMCP
from api_client import APIClient # Changed from relative for test compatibility
from utils.pagination import paginate_results, collect_all_results
from utils.validation import (
    validate_page_params,
    validate_sort_params,
    validate_study_id,
    validate_keyword,
    validate_gene_ids_list,
    validate_gene_id_type,
    validate_projection,
)
from utils.logging import setup_logging, get_logger
from endpoints import StudiesEndpoints, GenesEndpoints, SamplesEndpoints, MolecularProfilesEndpoints

# Ensure project root is in sys.path for utility imports if needed
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from utils.pagination_utils import paginate_results, collect_all_results # Example if utils were used

logger = get_logger(__name__)


class CBioPortalMCPServer:
    """MCP Server for interacting with the cBioPortal API."""

    def __init__(self, base_url: str = "https://www.cbioportal.org/api", client_timeout: float = 480.0):
        """Initialize the cBioPortal MCP Server with dependency injection."""
        self.base_url = base_url.rstrip('/')
        
        # Initialize API client
        self.api_client = APIClient(base_url=self.base_url, client_timeout=client_timeout)
        
        # Initialize endpoint modules with dependency injection
        self.studies = StudiesEndpoints(self.api_client)
        self.genes = GenesEndpoints(self.api_client)
        self.samples = SamplesEndpoints(self.api_client)
        self.molecular_profiles = MolecularProfilesEndpoints(self.api_client)
        
        # Initialize FastMCP instance
        self.mcp = FastMCP(
            name="cBioPortal",
            description="Access cancer genomics data from cBioPortal",
            instructions="This server provides tools to access and analyze cancer genomics data from cBioPortal.",
        )

        # Configure lifecycle hooks
        self.mcp.on_startup = [self.startup]
        self.mcp.on_shutdown = [self.shutdown]

        # Register MCP tools
        self._register_tools()

    async def startup(self):
        """Initialize async resources when server starts."""
        # self.client = httpx.AsyncClient(timeout=480.0) # Removed
        await self.api_client.startup() # Added
        logger.info("cBioPortal MCP Server started, APIClient initialized.") # Updated log

    async def shutdown(self):
        """Clean up async resources when server shuts down."""
        # if self.client: # Removed block
        #     await self.client.aclose()
        #     logger.info("cBioPortal MCP Server async HTTP client closed")
        if hasattr(self, 'api_client') and self.api_client: # Added
            await self.api_client.shutdown()
            logger.info("cBioPortal MCP Server APIClient shut down.") # Updated log
        else: # Added for completeness
            logger.info("cBioPortal MCP Server APIClient was not available or already shut down.")

    def _register_tools(self):
        """Register tool methods as MCP tools."""
        # List of methods to register as tools (explicitly defined)
        tool_methods = [
            # Pagination utilities
            "paginate_results",
            "collect_all_results",
            # Studies endpoints
            "get_cancer_studies",
            "get_cancer_types", 
            "search_studies",
            "get_study_details",
            "get_multiple_studies",
            # Genes endpoints
            "search_genes",
            "get_genes", 
            "get_multiple_genes",
            "get_mutations_in_gene",
            # Samples endpoints
            "get_samples_in_study",
            "get_sample_list_id",
            # Molecular profiles endpoints
            "get_molecular_profiles",
            "get_clinical_data",
            "get_gene_panels_for_study",
            "get_gene_panel_details",
        ]
        
        for method_name in tool_methods:
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                self.mcp.add_tool(method)
                logger.debug(f"Registered tool: {method_name}")
            else:
                logger.warning(f"Method {method_name} not found for tool registration")

    async def paginate_results(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        method: str = "GET",
        json_data: Any = None,
        max_pages: int = None,
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Delegate to utils.pagination.paginate_results with api_client."""
        async for page in paginate_results(
            self.api_client, endpoint, params, method, json_data, max_pages
        ):
            yield page

    async def collect_all_results(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        method: str = "GET",
        json_data: Any = None,
        max_pages: int = None,
        limit: int = None,
    ) -> List[Dict[str, Any]]:
        """Delegate to utils.pagination.collect_all_results with api_client."""
        return await collect_all_results(
            self.api_client, endpoint, params, method, json_data, max_pages, limit
        )

    # _make_api_request method was removed.
    # Its functionality is now handled by the APIClient class in api_client.py.


    # --- Collection-returning methods with pagination ---

    # --- Studies endpoints (delegated to StudiesEndpoints) ---
    
    async def get_cancer_studies(
        self,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get a list of cancer studies in cBioPortal with pagination support."""
        return await self.studies.get_cancer_studies(page_number, page_size, sort_by, direction, limit)

    async def get_cancer_types(
        self,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """Get a list of all available cancer types in cBioPortal with pagination support."""
        return await self.studies.get_cancer_types(page_number, page_size, sort_by, direction, limit)

    async def search_studies(
        self,
        keyword: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Search for cancer studies by keyword in their name or description with pagination support."""
        return await self.studies.search_studies(keyword, page_number, page_size, sort_by, direction, limit)

    async def get_study_details(self, study_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific cancer study."""
        return await self.studies.get_study_details(study_id)

    async def get_multiple_studies(self, study_ids: List[str]) -> Dict:
        """Get details for multiple studies concurrently."""
        return await self.studies.get_multiple_studies(study_ids)

    # --- Genes endpoints (delegated to GenesEndpoints) ---
    
    async def search_genes(
        self,
        keyword: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """Search for genes by keyword in their symbol or name with pagination support."""
        return await self.genes.search_genes(keyword, page_number, page_size, sort_by, direction, limit)

    async def get_genes(
        self,
        gene_ids: List[str],
        gene_id_type: str = "ENTREZ_GENE_ID",
        projection: str = "SUMMARY",
    ) -> Dict:
        """Get information about specific genes by their Hugo symbol or Entrez ID using batch endpoint."""
        return await self.genes.get_genes(gene_ids, gene_id_type, projection)

    async def get_multiple_genes(
        self,
        gene_ids: List[str],
        gene_id_type: str = "ENTREZ_GENE_ID",
        projection: str = "SUMMARY",
    ) -> Dict:
        """Get information about multiple genes concurrently."""
        return await self.genes.get_multiple_genes(gene_ids, gene_id_type, projection)

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
        """Get mutations in a specific gene for a given study and sample list, with pagination support."""
        return await self.genes.get_mutations_in_gene(gene_id, study_id, sample_list_id, page_number, page_size, sort_by, direction, limit)

    # --- Samples endpoints (delegated to SamplesEndpoints) ---
    
    async def get_samples_in_study(
        self,
        study_id: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """Get a list of samples associated with a specific cancer study with pagination support."""
        return await self.samples.get_samples_in_study(study_id, page_number, page_size, sort_by, direction, limit)

    async def get_sample_list_id(self, study_id: str, sample_list_id: str) -> Dict:
        """Get sample list information for a specific study and sample list ID."""
        return await self.samples.get_sample_list_id(study_id, sample_list_id)

    # --- Molecular Profiles endpoints (delegated to MolecularProfilesEndpoints) ---
    
    async def get_molecular_profiles(
        self,
        study_id: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """Get a list of molecular profiles available for a specific cancer study with pagination support."""
        return await self.molecular_profiles.get_molecular_profiles(study_id, page_number, page_size, sort_by, direction, limit)

    async def get_clinical_data(
        self,
        study_id: str,
        attribute_ids: Optional[List[str]] = None,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """Get clinical data for patients in a study with pagination support. Can fetch specific attributes or all."""
        return await self.molecular_profiles.get_clinical_data(study_id, attribute_ids, page_number, page_size, sort_by, direction, limit)

    async def get_gene_panels_for_study(
        self,
        study_id: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = "genePanelId",
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all gene panels in a specific study with pagination support."""
        return await self.molecular_profiles.get_gene_panels_for_study(study_id, page_number, page_size, sort_by, direction, limit)

    async def get_gene_panel_details(
        self,
        gene_panel_id: str,
        projection: str = "DETAILED",
    ) -> Dict[str, Any]:
        """Get detailed information for a specific gene panel, including the list of genes."""
        return await self.molecular_profiles.get_gene_panel_details(gene_panel_id, projection)



def handle_signal(signum, frame):
    logger.info(f"Signal {signum} received, initiating shutdown...")
    # Note: Actual shutdown logic might need to be coordinated with asyncio loop
    # For simplicity, we'll exit. FastMCP's run might handle this more gracefully.
    # frame parameter is required by signal handler signature but not used
    sys.exit(0)


def setup_signal_handlers():
    signal.signal(signal.SIGINT, handle_signal)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_signal)  # Handle termination


async def main():
    parser = argparse.ArgumentParser(description="Run the cBioPortal MCP Server.")
    parser.add_argument(
        "--base-url",
        default="https://www.cbioportal.org/api",
        help="Base URL for the cBioPortal API.",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio"],  # Limiting to stdio for now to simplify
        help="Transport protocol for MCP communication (currently only 'stdio' supported).",
    )
    # parser.add_argument(
    #     "--port",
    #     type=int,
    #     default=8000,
    #     help="Port for WebSocket transport (if used)."
    # )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )

    args = parser.parse_args()

    # Configure logging using utils
    setup_logging(level=args.log_level)
    global logger  # Use global logger after setup
    logger = get_logger(__name__)  # Re-assign to get logger with new config

    setup_signal_handlers()  # Setup signal handlers for graceful shutdown

    server_instance = CBioPortalMCPServer(base_url=args.base_url)

    logger.info(f"Starting cBioPortal MCP Server with transport: {args.transport}")

    if args.transport.lower() == "stdio":
        try:
            # Use run_async directly to avoid creating a new event loop
            # This is needed for compatibility with Claude Desktop which already has an event loop
            await server_instance.mcp.run_async(transport="stdio")
        except KeyboardInterrupt:
            logger.info("Server interrupted by user (KeyboardInterrupt).")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during server execution: {e}",
                exc_info=True,
            )
        finally:
            logger.info("Server shutdown sequence initiated from main.")
            # Explicitly call shutdown hooks if not handled by FastMCP
            if hasattr(server_instance, 'api_client') and server_instance.api_client is not None:
                await server_instance.shutdown()
            # For now, assuming FastMCP handles it.
    else:
        logger.error(f"Unsupported transport: {args.transport}")
        sys.exit(1)

    logger.info("cBioPortal MCP Server has shut down.")


def cli_main():
    """Synchronous entry point for CLI script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()

# End of file
