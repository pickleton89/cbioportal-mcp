#!/usr/bin/env python3
# Tests for basic functionality of the cBioPortal MCP Server

import sys
import os
import pytest
from unittest.mock import patch, call

# Add the parent directory to the path so we can import the cbioportal_server module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


# Pytest Fixtures
# Fixtures have been moved to tests/conftest.py


# Test Functions
# All test functions have been moved to more specific files (e.g., test_multiple_entity_apis.py)


# Original content related to get_multiple_studies and get_multiple_genes tests is now removed.

# The file is intentionally left with this structure in case top-level
# or general server tests (not specific to API categories) are needed later.
