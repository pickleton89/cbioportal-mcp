"""
Utility modules for the cBioPortal MCP server.

This package contains common utilities used across the server:
- pagination: Pagination handling and result collection
- validation: Input validation helpers
- logging: Centralized logging configuration
"""

from .pagination import paginate_results, collect_all_results
from .validation import (
    validate_page_params,
    validate_study_id,
    validate_gene_id,
    validate_sort_params,
)
from .logging import setup_logging, get_logger

__all__ = [
    "paginate_results",
    "collect_all_results",
    "validate_page_params",
    "validate_study_id", 
    "validate_gene_id",
    "validate_sort_params",
    "setup_logging",
    "get_logger",
]