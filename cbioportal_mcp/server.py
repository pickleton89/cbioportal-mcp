#!/usr/bin/env python3
"""
cBioPortal MCP Server (clean implementation)
Provides Model Context Protocol tools for accessing the cBioPortal API with full pagination support.
"""

import argparse
import asyncio
import signal
import sys
from typing import Any, Dict, List, Optional, AsyncGenerator

from fastmcp import FastMCP
from .api_client import APIClient
from .utils.pagination import paginate_results, collect_all_results
from .utils.logging import setup_logging, get_logger
from .endpoints import (
    StudiesEndpoints,
    GenesEndpoints,
    SamplesEndpoints,
    MolecularProfilesEndpoints,
)
from .config import load_config, create_example_config, Configuration

# Ensure project root is in sys.path for utility imports if needed
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from utils.pagination_utils import paginate_results, collect_all_results # Example if utils were used

logger = get_logger(__name__)


class CBioPortalMCPServer:
    """MCP Server for interacting with the cBioPortal API."""

    def __init__(self, config: Configuration):
        """Initialize the cBioPortal MCP Server with dependency injection."""
        self.config = config
        self.base_url = config.get("server.base_url").rstrip("/")

        # Initialize API client
        client_timeout = config.get("server.client_timeout")
        self.api_client = APIClient(
            base_url=self.base_url, client_timeout=client_timeout
        )

        # Initialize endpoint modules with dependency injection
        self.studies = StudiesEndpoints(self.api_client)
        self.genes = GenesEndpoints(self.api_client, config)
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
        await self.api_client.startup()  # Added
        logger.info(
            "cBioPortal MCP Server started, APIClient initialized."
        )  # Updated log

    async def shutdown(self):
        """Clean up async resources when server shuts down."""
        # if self.client: # Removed block
        #     await self.client.aclose()
        #     logger.info("cBioPortal MCP Server async HTTP client closed")
        if hasattr(self, "api_client") and self.api_client:  # Added
            await self.api_client.shutdown()
            logger.info("cBioPortal MCP Server APIClient shut down.")  # Updated log
        else:  # Added for completeness
            logger.info(
                "cBioPortal MCP Server APIClient was not available or already shut down."
            )

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
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        json_data: Any = None,
        max_pages: Optional[int] = None,
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Delegate to utils.pagination.paginate_results with api_client."""
        async for page in paginate_results(
            self.api_client, endpoint, params, method, json_data, max_pages
        ):
            yield page

    async def collect_all_results(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        json_data: Any = None,
        max_pages: Optional[int] = None,
        limit: Optional[int] = None,
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
        return await self.studies.get_cancer_studies(
            page_number, page_size, sort_by, direction, limit
        )

    async def get_cancer_types(
        self,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None,
    ) -> Dict:
        """Get a list of all available cancer types in cBioPortal with pagination support."""
        return await self.studies.get_cancer_types(
            page_number, page_size, sort_by, direction, limit
        )

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
        return await self.studies.search_studies(
            keyword, page_number, page_size, sort_by, direction, limit
        )

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
        return await self.genes.search_genes(
            keyword, page_number, page_size, sort_by, direction, limit
        )

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
        return await self.genes.get_mutations_in_gene(
            gene_id,
            study_id,
            sample_list_id,
            page_number,
            page_size,
            sort_by,
            direction,
            limit,
        )

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
        return await self.samples.get_samples_in_study(
            study_id, page_number, page_size, sort_by, direction, limit
        )

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
        return await self.molecular_profiles.get_molecular_profiles(
            study_id, page_number, page_size, sort_by, direction, limit
        )

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
        return await self.molecular_profiles.get_clinical_data(
            study_id, attribute_ids, page_number, page_size, sort_by, direction, limit
        )

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
        return await self.molecular_profiles.get_gene_panels_for_study(
            study_id, page_number, page_size, sort_by, direction, limit
        )

    async def get_gene_panel_details(
        self,
        gene_panel_id: str,
        projection: str = "DETAILED",
    ) -> Dict[str, Any]:
        """Get detailed information for a specific gene panel, including the list of genes."""
        return await self.molecular_profiles.get_gene_panel_details(
            gene_panel_id, projection
        )


def setup_signal_handlers():
    """
    Set up signal handlers for graceful shutdown.

    For async applications, it's better to let the KeyboardInterrupt
    exception bubble up naturally rather than using signal handlers
    that call sys.exit(). This allows proper cleanup in the finally block.
    """
    # Modern async Python applications typically handle SIGINT via KeyboardInterrupt
    # and SIGTERM through the event loop, rather than custom signal handlers
    # that call sys.exit(). This allows proper async cleanup.

    def handle_sigterm(signum, frame):
        """Handle SIGTERM by raising KeyboardInterrupt to trigger cleanup."""
        logger.info("SIGTERM received, initiating graceful shutdown...")
        # Instead of sys.exit(), raise KeyboardInterrupt to let the async cleanup handle it
        raise KeyboardInterrupt("SIGTERM received")

    # Only handle SIGTERM since SIGINT is naturally handled as KeyboardInterrupt
    signal.signal(signal.SIGTERM, handle_sigterm)


async def main():
    parser = argparse.ArgumentParser(
        description="Run the cBioPortal MCP Server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration Sources (in priority order):
  1. CLI arguments (highest priority)
  2. Environment variables (CBIOPORTAL_*)
  3. Configuration file (--config)
  4. Default values (lowest priority)

Examples:
  %(prog)s                                    # Use defaults
  %(prog)s --config config.yaml             # Use config file
  %(prog)s --base-url https://custom.org/api # Override base URL
  %(prog)s --create-example-config           # Create example config
        """,
    )

    # Configuration file support
    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML configuration file.",
    )
    parser.add_argument(
        "--create-example-config",
        type=str,
        nargs="?",
        const="cbioportal-mcp-config.example.yaml",
        help="Create an example configuration file and exit. Optionally specify filename.",
    )

    # Server configuration
    parser.add_argument(
        "--base-url",
        help="Base URL for the cBioPortal API. (overrides config file)",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio"],
        help="Transport protocol for MCP communication. (overrides config file)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port for WebSocket transport (for future use). (overrides config file)",
    )

    # Logging configuration
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level. (overrides config file)",
    )

    args = parser.parse_args()

    # Handle example config creation
    if args.create_example_config:
        try:
            create_example_config(args.create_example_config)
            print(f"Example configuration created: {args.create_example_config}")
            print(
                f"Edit the file and use: {parser.prog} --config {args.create_example_config}"
            )
            return
        except Exception as e:
            print(f"Error creating example config: {e}", file=sys.stderr)
            sys.exit(1)

    # Load configuration
    try:
        config = load_config(args.config)

        # Update config with CLI arguments
        cli_args = {}
        if args.base_url is not None:
            cli_args["base_url"] = args.base_url
        if args.transport is not None:
            cli_args["transport"] = args.transport
        if args.port is not None:
            cli_args["port"] = args.port
        if args.log_level is not None:
            cli_args["log_level"] = args.log_level

        if cli_args:
            config.update_from_cli_args(cli_args)

    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Configure logging using the loaded configuration
    log_level = config.get("logging.level")
    setup_logging(level=log_level)
    # Get logger with new configuration - no global reassignment needed
    config_logger = get_logger(__name__)

    setup_signal_handlers()  # Setup signal handlers for graceful shutdown

    # Log configuration info
    config_logger.info("Starting cBioPortal MCP Server")
    config_logger.info(f"Base URL: {config.get('server.base_url')}")
    config_logger.info(f"Transport: {config.get('server.transport')}")
    config_logger.info(f"Client timeout: {config.get('server.client_timeout')}s")
    if args.config:
        config_logger.info(f"Configuration file: {args.config}")

    server_instance = CBioPortalMCPServer(config=config)

    transport = config.get("server.transport")
    config_logger.info(f"Using transport: {transport}")

    if transport.lower() == "stdio":
        try:
            # Use run_async directly to avoid creating a new event loop
            # This is needed for compatibility with Claude Desktop which already has an event loop
            await server_instance.mcp.run_async(transport="stdio")
        except KeyboardInterrupt as e:
            # Handle both Ctrl+C and SIGTERM gracefully
            interrupt_msg = str(e) if str(e) else "user interrupt (Ctrl+C)"
            config_logger.info(f"Server interrupted by {interrupt_msg}.")
        except Exception as e:
            config_logger.error(
                f"An unexpected error occurred during server execution: {e}",
                exc_info=True,
            )
        finally:
            config_logger.info("Server shutdown sequence initiated from main.")
            # Explicitly call shutdown hooks if not handled by FastMCP
            if (
                hasattr(server_instance, "api_client")
                and server_instance.api_client is not None
            ):
                await server_instance.shutdown()
            # For now, assuming FastMCP handles it.
    else:
        config_logger.error(f"Unsupported transport: {transport}")
        sys.exit(1)

    config_logger.info("cBioPortal MCP Server has shut down.")


def cli_main():
    """Synchronous entry point for CLI script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()

# End of file
