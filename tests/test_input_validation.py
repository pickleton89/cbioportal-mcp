#!/usr/bin/env python3
# Tests for input validation in the cBioPortal MCP Server

import pytest


class TestInputValidation:
    """Tests for input validation of CBioPortalMCPServer methods."""

    @pytest.fixture(scope="class")
    def server_instance(self, cbioportal_server_instance):
        """Provides a CBioPortalMCPServer instance for the test class."""
        # No need to mock httpx.AsyncClient for input validation tests
        # as errors should be raised before API calls.
        return cbioportal_server_instance

    @pytest.mark.parametrize(
        "page_number, page_size, expected_exception, error_match",
        [
            (-1, 50, ValueError, "page_number must be non-negative"),
            ("abc", 50, TypeError, "page_number must be an integer"),
            (0, 0, ValueError, "page_size must be positive"),
            (0, -10, ValueError, "page_size must be positive"),
            (0, "xyz", TypeError, "page_size must be an integer"),
        ],
    )
    async def test_get_cancer_studies_invalid_pagination(self, server_instance, page_number, page_size, expected_exception, error_match):
        """Test get_cancer_studies with invalid page_number or page_size."""
        with pytest.raises(expected_exception, match=error_match):
            await server_instance.get_cancer_studies(page_number=page_number, page_size=page_size)

    @pytest.mark.parametrize(
        "study_id, expected_exception, error_match",
        [
            ("", ValueError, "study_id cannot be empty"),
            (None, TypeError, "study_id must be a string"),
            (123, TypeError, "study_id must be a string"),
            (["study1"], TypeError, "study_id must be a string"), # Test with a list
        ],
    )
    async def test_get_study_details_invalid_study_id(self, server_instance, study_id, expected_exception, error_match):
        """Test get_study_details with invalid study_id."""
        with pytest.raises(expected_exception, match=error_match):
            await server_instance.get_study_details(study_id=study_id)

    @pytest.mark.parametrize(
        "page_number, page_size, expected_exception, error_match",
        [
            (-1, 50, ValueError, "page_number must be non-negative"),
            ("abc", 50, TypeError, "page_number must be an integer"),
            (0, 0, ValueError, "page_size must be positive"),
            (0, -10, ValueError, "page_size must be positive"),
            (0, "xyz", TypeError, "page_size must be an integer"),
        ],
    )
    async def test_get_cancer_types_invalid_pagination(self, server_instance, page_number, page_size, expected_exception, error_match):
        """Test get_cancer_types with invalid page_number or page_size."""
        with pytest.raises(expected_exception, match=error_match):
            await server_instance.get_cancer_types(page_number=page_number, page_size=page_size)

    @pytest.mark.parametrize(
        "study_id, page_number, page_size, expected_exception, error_match",
        [
            # Invalid study_id
            ("", 0, 50, ValueError, "study_id cannot be empty"),
            (None, 0, 50, TypeError, "study_id must be a string"),
            (123, 0, 50, TypeError, "study_id must be a string"),
            # Invalid page_number
            ("valid_study", -1, 50, ValueError, "page_number must be non-negative"),
            ("valid_study", "abc", 50, TypeError, "page_number must be an integer"),
            # Invalid page_size
            ("valid_study", 0, 0, ValueError, "page_size must be positive"),
            ("valid_study", 0, "xyz", TypeError, "page_size must be an integer"),
        ],
    )
    async def test_get_molecular_profiles_invalid_inputs(self, server_instance, study_id, page_number, page_size, expected_exception, error_match):
        """Test get_molecular_profiles with invalid study_id or pagination parameters."""
        with pytest.raises(expected_exception, match=error_match):
            await server_instance.get_molecular_profiles(study_id=study_id, page_number=page_number, page_size=page_size)

    @pytest.mark.parametrize(
        "study_id, page_number, page_size, expected_exception, error_match",
        [
            # Invalid study_id
            ("", 0, 50, ValueError, "study_id cannot be empty"),
            (None, 0, 50, TypeError, "study_id must be a string"),
            (123, 0, 50, TypeError, "study_id must be a string"),
            # Invalid page_number
            ("valid_study", -1, 50, ValueError, "page_number must be non-negative"),
            ("valid_study", "abc", 50, TypeError, "page_number must be an integer"),
            # Invalid page_size
            ("valid_study", 0, 0, ValueError, "page_size must be positive"),
            ("valid_study", 0, "xyz", TypeError, "page_size must be an integer"),
        ],
    )
    async def test_get_samples_in_study_invalid_inputs(self, server_instance, study_id, page_number, page_size, expected_exception, error_match):
        """Test get_samples_in_study with invalid study_id or pagination parameters."""
        with pytest.raises(expected_exception, match=error_match):
            await server_instance.get_samples_in_study(study_id=study_id, page_number=page_number, page_size=page_size)

    @pytest.mark.parametrize(
        "keyword, page_number, page_size, expected_exception, error_match",
        [
            # Invalid keyword
            ("", 0, 50, ValueError, "keyword cannot be empty"),
            (None, 0, 50, TypeError, "keyword must be a string"),
            (123, 0, 50, TypeError, "keyword must be a string"),
            # Invalid page_number
            ("BRCA", -1, 50, ValueError, "page_number must be non-negative"),
            ("BRCA", "abc", 50, TypeError, "page_number must be an integer"),
            # Invalid page_size
            ("BRCA", 0, 0, ValueError, "page_size must be positive"),
            ("BRCA", 0, "xyz", TypeError, "page_size must be an integer"),
        ],
    )
    async def test_search_genes_invalid_inputs(self, server_instance, keyword, page_number, page_size, expected_exception, error_match):
        """Test search_genes with invalid keyword or pagination parameters."""
        with pytest.raises(expected_exception, match=error_match):
            await server_instance.search_genes(keyword=keyword, page_number=page_number, page_size=page_size)

    @pytest.mark.parametrize(
        "keyword, page_number, page_size, expected_exception, error_match",
        [
            # Invalid keyword
            ("", 0, 50, ValueError, "keyword cannot be empty"),
            (None, 0, 50, TypeError, "keyword must be a string"),
            (123, 0, 50, TypeError, "keyword must be a string"),
            # Invalid page_number
            ("ACC_TCGA", -1, 50, ValueError, "page_number must be non-negative"),
            ("ACC_TCGA", "abc", 50, TypeError, "page_number must be an integer"),
            # Invalid page_size
            ("ACC_TCGA", 0, 0, ValueError, "page_size must be positive"),
            ("ACC_TCGA", 0, "xyz", TypeError, "page_size must be an integer"),
        ],
    )
    async def test_search_studies_invalid_inputs(self, server_instance, keyword, page_number, page_size, expected_exception, error_match):
        """Test search_studies with invalid keyword or pagination parameters."""
        with pytest.raises(expected_exception, match=error_match):
            await server_instance.search_studies(keyword=keyword, page_number=page_number, page_size=page_size)

