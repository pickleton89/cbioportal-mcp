import pytest
from unittest.mock import patch, call
import sys
import os

# Add the parent directory to the path so we can import the cbioportal_server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cbioportal_server import CBioPortalMCPServer


@pytest.fixture
def cbioportal_server_instance():
    return CBioPortalMCPServer(base_url="https://www.cbioportal.org/api")


@pytest.fixture
def mock_studies_data_page_1():
    return [
        {
            "studyId": f"study_{i}",
            "name": f"Study {i}",
            "description": f"Description {i}",
        }
        for i in range(1, 4)
    ]


@pytest.fixture
def mock_studies_data_page_2():
    return [
        {
            "studyId": f"study_{i}",
            "name": f"Study {i}",
            "description": f"Description {i}",
        }
        for i in range(4, 7)
    ]


@pytest.fixture
def mock_studies_data_last_page_less_than_pagesize():
    return [
        {
            "studyId": f"study_{i}",
            "name": f"Study {i}",
            "description": f"Description {i}",
        }
        for i in range(7, 9)
    ]


@pytest.fixture
def mock_studies_data_last_page_exact_pagesize():
    return [
        {
            "studyId": f"study_{i}",
            "name": f"Study {i}",
            "description": f"Description {i}",
        }
        for i in range(9, 12)
    ]


@pytest.fixture
def mock_cancer_types_data():
    return [
        {"cancerTypeId": f"type_{i}", "name": f"Cancer Type {i}"} 
        for i in range(1, 51)
    ]


@pytest.fixture
def mock_samples_data():
    return [
        {"sampleId": f"sample_{i}", "patientId": f"patient_{i % 20}", "studyId": "study_1"} 
        for i in range(1, 201)
    ]


@pytest.fixture
def mock_mutations_data_page_1():
    return [
        {
            "uniqueSampleKey": f"sample_{i}_study_1",
            "uniquePatientKey": f"patient_{i % 20}_study_1",
            "molecularProfileId": "profile_1",
            "sampleId": f"sample_{i}",
            "patientId": f"patient_{i % 20}",
            "studyId": "study_1",
            "gene": {"hugoGeneSymbol": "GENE1", "entrezGeneId": 123},
            "mutationEffect": "MISSENSE",
            "mutationStatus": "SOMATIC",
            "mutationType": "SNP",
            "proteinChange": "p.V600E",
            "keyword": "V600E",
        }
        for i in range(1, 3)
    ]


@pytest.fixture
def mock_molecular_profiles_for_mutations_test():
    return [
        {
            "molecularProfileId": "brca_tcga_pan_can_atlas_2018_mutations",
            "studyId": "brca_tcga_pan_can_atlas_2018",
            "name": "BRCA TCGA PanCanAtlas 2018 Mutations",
            "molecularAlterationType": "MUTATION_EXTENDED",
            "datatype": "MAF",
            "showProfileInAnalysisTab": True
        }
    ]


@pytest.fixture
def mock_clinical_data_page_1():
    return [
        {
            "uniqueSampleKey": f"sample_{i}_study_1",
            "uniquePatientKey": f"patient_{i % 10}_study_1",
            "clinicalAttributeId": "ATTR_1",
            "patientId": f"patient_{i % 10}",
            "sampleId": f"sample_{i}",
            "studyId": "study_1",
            "value": f"Value {i}",
        }
        for i in range(1, 3)
    ]


@pytest.fixture
def mock_clinical_attributes_data():
    return [
        {
            "clinicalAttributeId": f"ATTR_{i}", 
            "displayName": f"Attribute {i}", 
            "description": f"Description for Attribute {i}", 
            "datatype": "STRING", 
            "patientAttribute": True
        }
        for i in range(1, 76)
    ]


@pytest.fixture
def mock_genes_data():
    return [
        {
            "entrezGeneId": i,
            "hugoGeneSymbol": f"GENE{i}",
            "type": "protein-coding",
            "oncogene": i % 2 == 0,
            "tsg": i % 2 != 0,
        }
        for i in range(1, 151)
    ]


@pytest.fixture
def mock_molecular_profiles_data_all():
    return [
        {
            "molecularProfileId": f"profile_{i}",
            "studyId": f"study_{(i % 5) + 1}",
            "name": f"Molecular Profile {i}",
            "molecularAlterationType": "MUTATION_EXTENDED",
            "datatype": "MAF",
            "showProfileInAnalysisTab": True
        }
        for i in range(1, 61)
    ]


# Define test cases for get_cancer_studies pagination
cancer_studies_test_cases = [
    pytest.param(
        "first_page",         # scenario_name
        0,                    # page_number
        "mock_studies_data_page_1",  # mock_data_fixture_name
        True,                 # expected_has_more
        3,                    # page_size_to_use
        id="first_page_full"
    ),
    pytest.param(
        "second_page",
        1,
        "mock_studies_data_page_2",
        True,
        3,
        id="second_page_full"
    ),
    pytest.param(
        "last_page_partial",
        2,
        "mock_studies_data_last_page_less_than_pagesize",
        False, # API returns less than page_size, so server says no more
        3,
        id="last_page_less_than_pagesize"
    ),
    pytest.param(
        "last_page_full",
        3,
        "mock_studies_data_last_page_exact_pagesize",
        True, # API returns exactly page_size, so server says more might exist
        3,
        id="last_page_exact_pagesize"
    ),
]

@pytest.mark.asyncio
@patch("api_client.APIClient.make_api_request")
@pytest.mark.parametrize(
    "scenario_name, page_number, mock_data_fixture_name, expected_has_more, page_size_to_use",
    cancer_studies_test_cases
)
async def test_get_cancer_studies_pagination(
    mock_api_request, 
    cbioportal_server_instance,
    request, # Pytest request fixture to dynamically get other fixtures
    scenario_name, 
    page_number, 
    mock_data_fixture_name, 
    expected_has_more, 
    page_size_to_use
):
    server = cbioportal_server_instance
    
    # Dynamically get the mock data fixture by its name
    mock_data = request.getfixturevalue(mock_data_fixture_name)
    mock_api_request.return_value = mock_data
    
    expected_items_count = len(mock_data)

    result = await server.get_cancer_studies(page_number=page_number, page_size=page_size_to_use)
    
    assert len(result["studies"]) == expected_items_count
    assert result["pagination"]["page"] == page_number
    assert result["pagination"]["has_more"] is expected_has_more
    mock_api_request.assert_called_with(
        "studies", params={"pageNumber": page_number, "pageSize": page_size_to_use, "direction": "ASC"}
    )


@pytest.mark.asyncio
@patch("api_client.APIClient.make_api_request")
async def test_get_mutations_in_gene_pagination(
    mock_api_request,
    cbioportal_server_instance,
    mock_mutations_data_page_1,
    mock_molecular_profiles_for_mutations_test, # Mock for the internal molecular profile fetch
):
    server = cbioportal_server_instance
    gene_id = "TP53"
    study_id = "brca_tcga_pan_can_atlas_2018"
    sample_list_id = f"{study_id}_all" # Required by the server method
    page_size = 2 # Must match mock data for has_more logic

    # Setup side_effect for the two internal calls:
    # 1. Fetch molecular profiles for the study
    # 2. Fetch mutations for the determined molecular profile
    mock_api_request.side_effect = [
        mock_molecular_profiles_for_mutations_test, # First call
        mock_mutations_data_page_1                 # Second call
    ]

    result = await server.get_mutations_in_gene(
        gene_id=gene_id,
        study_id=study_id,
        sample_list_id=sample_list_id,
        page_number=0,
        page_size=page_size,
    )

    assert len(result["mutations"]) == page_size
    assert result["pagination"]["page"] == 0
    assert result["pagination"]["has_more"] is True

    # Assert the first call to get molecular profiles
    mock_api_request.assert_any_call(f"studies/{study_id}/molecular-profiles")

    # Assert the second call to get mutations (assuming a mutation_profile_id was found)
    # This requires knowing/mocking the mutation_profile_id that would be selected.
    # For this test, let's assume 'brca_tcga_pan_can_atlas_2018_mutations' is selected from the mock.
    expected_mutation_profile_id = "brca_tcga_pan_can_atlas_2018_mutations"
    mock_api_request.assert_called_with(
        f"molecular-profiles/{expected_mutation_profile_id}/mutations",
        method="GET",
        params={
            "studyId": study_id,
            "sampleListId": sample_list_id,
            "pageNumber": 0,
            "pageSize": page_size,
            "direction": "ASC",
            "hugoGeneSymbol": gene_id,
        },
    )


@pytest.mark.asyncio
@patch("api_client.APIClient.make_api_request")
async def test_get_clinical_data_pagination(
    mock_api_request,
    cbioportal_server_instance, mock_clinical_data_page_1
):
    server = cbioportal_server_instance
    study_id = "acc_tcga"
    page_size = 2 # Must match mock data for has_more

    mock_api_request.return_value = mock_clinical_data_page_1
    result = await server.get_clinical_data(
        study_id=study_id, page_number=0, page_size=page_size
    )

    # The server method transforms the flat list into a dict by patientId
    # So, len(result["clinical_data_by_patient"]) is the count of unique patients.
    # The mock_clinical_data_page_1 contains 2 items for 2 unique patients.
    assert len(result["clinical_data_by_patient"]) == 2
    assert result["pagination"]["page"] == 0
    assert result["pagination"]["has_more"] is True # Based on page_size vs items from API

    mock_api_request.assert_called_with(
        f"studies/{study_id}/clinical-data",
        method="GET",
        params={"pageNumber": 0, "pageSize": page_size, "direction": "ASC", "clinicalDataType": "PATIENT"},
    )


@pytest.mark.asyncio
@patch("api_client.APIClient.make_api_request")
async def test_get_molecular_profiles_pagination(
    mock_api_request,
    cbioportal_server_instance, mock_molecular_profiles_data_all # Use a mock that represents all profiles
):
    server = cbioportal_server_instance
    study_id = "study_123" # Example study_id
    page_size = 2 # Server will paginate client-side from the full list

    # Server fetches all profiles first, then paginates them.
    mock_api_request.return_value = mock_molecular_profiles_data_all

    result = await server.get_molecular_profiles(
        study_id=study_id, page_number=0, page_size=page_size
    )

    # Assuming mock_molecular_profiles_data_all has more than 'page_size' items
    assert len(result["molecular_profiles"]) == page_size
    assert result["pagination"]["page"] == 0
    assert result["pagination"]["has_more"] is True

    # The API call should be to fetch all profiles for the study, without pagination params
    mock_api_request.assert_called_with(f"studies/{study_id}/molecular-profiles")


@pytest.mark.asyncio
@patch("api_client.APIClient.make_api_request")
async def test_paginate_results_basic(mock_make_api_request, cbioportal_server_instance):
    server = cbioportal_server_instance
    endpoint = "studies"
    page_size = 2
    mock_page_1_data = [{"id": 1}, {"id": 2}]
    mock_page_2_data = [{"id": 3}, {"id": 4}]
    mock_empty_page_data = []

    # Configure the mock to return different data for sequential calls
    mock_make_api_request.side_effect = [
        mock_page_1_data,
        mock_page_2_data,
        mock_empty_page_data, # Signifies no more data
    ]

    collected_results = []
    async for page_data in server.paginate_results(endpoint, params={"pageSize": page_size}):
        collected_results.extend(page_data)

    assert collected_results == mock_page_1_data + mock_page_2_data

    expected_calls = [
        call(endpoint, method="GET", params={"pageNumber": 0, "pageSize": page_size}, json_data=None),
        call(endpoint, method="GET", params={"pageNumber": 1, "pageSize": page_size}, json_data=None),
        call(endpoint, method="GET", params={"pageNumber": 2, "pageSize": page_size}, json_data=None), # This call returns empty
    ]
    mock_make_api_request.assert_has_calls(expected_calls)
    assert mock_make_api_request.call_count == 3


@pytest.mark.asyncio
@patch("api_client.APIClient.make_api_request")
async def test_paginate_results_empty_first_call(mock_make_api_request, cbioportal_server_instance):
    server = cbioportal_server_instance
    endpoint = "studies"
    page_size = 2
    mock_empty_page_data = []

    mock_make_api_request.return_value = mock_empty_page_data

    collected_results = []
    async for page_data in server.paginate_results(
        endpoint, 
        params={"pageNumber": 0, "pageSize": page_size}
    ):
        collected_results.extend(page_data)

    assert collected_results == []

    # Expect only one call, which returns empty
    expected_calls = [
        call(endpoint, method="GET", params={"pageNumber": 0, "pageSize": page_size}, json_data=None),
    ]
    mock_make_api_request.assert_has_calls(expected_calls)
    assert mock_make_api_request.call_count == 1


@pytest.mark.asyncio
@patch("api_client.APIClient.make_api_request")
async def test_paginate_results_with_max_pages(mock_make_api_request, cbioportal_server_instance):
    server = cbioportal_server_instance
    endpoint = "studies"
    page_size = 1
    max_pages_to_fetch = 2

    # Mock API to simulate more data than max_pages
    mock_page_1_data = [{"id": 1}]
    mock_page_2_data = [{"id": 2}]
    mock_page_3_data = [{"id": 3}] # This page should not be fetched

    mock_make_api_request.side_effect = [
        mock_page_1_data,
        mock_page_2_data,
        mock_page_3_data, 
    ]

    collected_results = []
    async for page_data in server.paginate_results(
        endpoint, 
        params={"pageNumber": 0, "pageSize": page_size}, 
        max_pages=max_pages_to_fetch
    ):
        collected_results.extend(page_data)

    assert collected_results == mock_page_1_data + mock_page_2_data

    expected_calls = [
        call(endpoint, method="GET", params={"pageNumber": 0, "pageSize": page_size}, json_data=None),
        call(endpoint, method="GET", params={"pageNumber": 1, "pageSize": page_size}, json_data=None),
        # No call for pageNumber 2 because max_pages is 2
    ]
    mock_make_api_request.assert_has_calls(expected_calls)
    assert mock_make_api_request.call_count == 2 # Should only call API twice


@pytest.mark.asyncio
@patch("api_client.APIClient.make_api_request")
async def test_paginate_results_last_page_partial(mock_make_api_request, cbioportal_server_instance):
    server = cbioportal_server_instance
    endpoint = "studies"
    page_size = 3

    mock_page_1_data = [{"id": 1}, {"id": 2}, {"id": 3}] # Full page
    mock_page_2_partial_data = [{"id": 4}, {"id": 5}]    # Partial page, less than page_size

    mock_make_api_request.side_effect = [
        mock_page_1_data,
        mock_page_2_partial_data,
    ]

    collected_results = []
    async for page_data in server.paginate_results(
        endpoint, 
        params={"pageNumber": 0, "pageSize": page_size}
    ):
        collected_results.extend(page_data)

    assert collected_results == mock_page_1_data + mock_page_2_partial_data

    expected_calls = [
        call(endpoint, method="GET", params={"pageNumber": 0, "pageSize": page_size}, json_data=None),
        call(endpoint, method="GET", params={"pageNumber": 1, "pageSize": page_size}, json_data=None),
    ]
    mock_make_api_request.assert_has_calls(expected_calls)
    assert mock_make_api_request.call_count == 2 # API called for page 0 and page 1
