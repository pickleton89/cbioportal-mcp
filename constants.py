"""
Constants used throughout the cBioPortal MCP server.

This module contains shared constants to avoid magic numbers and
improve maintainability.
"""

# Pagination constants
DEFAULT_PAGE_SIZE = 50
DEFAULT_PAGE_NUMBER = 0
MAX_PAGE_SIZE = 10000

# When we want to fetch "all" results in a single request,
# we use this large page size value
FETCH_ALL_PAGE_SIZE = 10000000

# API response constants
DEFAULT_SORT_DIRECTION = "ASC"

# Timeout constants (in seconds)
DEFAULT_API_TIMEOUT = 30
LONG_RUNNING_API_TIMEOUT = 480

# Clinical data types
CLINICAL_DATA_TYPES = ["PATIENT", "SAMPLE"]

# Molecular alteration types
MOLECULAR_ALTERATION_TYPES = [
    "MUTATION_EXTENDED",
    "COPY_NUMBER_ALTERATION", 
    "MRNA_EXPRESSION",
    "PROTEIN_EXPRESSION",
    "METHYLATION"
]