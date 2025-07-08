"""
Endpoint modules for the cBioPortal MCP server.

This package contains modular endpoint implementations organized by domain:
- studies: Cancer study related endpoints
- genes: Gene and mutation related endpoints  
- samples: Sample related endpoints
- molecular_profiles: Molecular profile and clinical data endpoints
"""

from .studies import StudiesEndpoints
from .genes import GenesEndpoints
from .samples import SamplesEndpoints
from .molecular_profiles import MolecularProfilesEndpoints

__all__ = [
    "StudiesEndpoints",
    "GenesEndpoints", 
    "SamplesEndpoints",
    "MolecularProfilesEndpoints",
]