# tests/test_snapshot_responses.py
import pytest
from unittest.mock import AsyncMock

from syrupy.assertion import SnapshotAssertion

from cbioportal_mcp.server import CBioPortalMCPServer

@pytest.fixture
def server_instance(cbioportal_server_instance): # Use the standard fixture from conftest
    """Provides a CBioPortalMCPServer instance."""
    # The cbioportal_server_instance fixture from conftest.py already provides
    # a server with an initialized APIClient. We will mock the APIClient's
    # make_api_request method directly in each test.
    return cbioportal_server_instance

@pytest.mark.asyncio
async def test_get_study_details_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from get_study_details matches the snapshot."""
    study_id_to_test = "acc_tcga"
    
    # Mock the API response
    mock_response_data = {
        "studyId": "acc_tcga",
        "name": "Adrenocortical Carcinoma (TCGA, PanCancer Atlas)",
        "description": "TCGA PanCanAtlas ACC",
        "publicStudy": True,
        "pmid": "29622464",
        "citation": "Cancer Genome Atlas Research Network. (2018). The Immune Landscape of Cancer. Immunity, 48(4).",
        "groups": "PANCANCER;PANCAN",
        "status": 0,
        "importDate": "2018-04-10 00:00:00",
        "allSampleCount": 92,
        "sequencedSampleCount": 90,
        "cnaSampleCount": 90,
        "mrnaRnaSeqSampleCount": 79,
        "mrnaRnaSeqV2SampleCount": 0,
        "mrnaMicroarraySampleCount": 0,
        "methylationHm27SampleCount": 0,
        "miRnaSampleCount": 0,
        "rppaSampleCount": 0,
        "massSpectrometrySampleCount": 0,
        "svSampleCount": 0,
        "referenceGenome": "hg19",
        "cancerType": {
            "cancerTypeId": "acc",
            "name": "Adrenocortical Carcinoma",
            "dedicatedColor": "LightGreen",
            "shortName": "ACC",
            "parentCancerTypeId": "adrenal_gland"
        },
        "cancerTypeId": "acc",
        "numberOfSamplesWithCompleteSampleData": 90,
        "readPermission": True
    }
    
    # Configure the mock client's _make_api_request method
    mock_api_request = AsyncMock(return_value=mock_response_data)
    server_instance.api_client.make_api_request = mock_api_request # type: ignore

    response = await server_instance.get_study_details(study_id=study_id_to_test)
    
    assert response == snapshot

@pytest.mark.asyncio
async def test_get_cancer_studies_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from get_cancer_studies matches the snapshot."""
    # Mock the API response for get_cancer_studies
    mock_studies_data = [
        {
            "studyId": "acc_tcga",
            "name": "Adrenocortical Carcinoma (TCGA, PanCancer Atlas)",
            "description": "TCGA PanCanAtlas ACC",
            "publicStudy": True,
            "cancerTypeId": "acc",
            "referenceGenome": "hg19",
            "pmid": "29622464",
            "citation": "Cancer Genome Atlas Research Network. (2018). The Immune Landscape of Cancer. Immunity, 48(4).",
            "groups": "PANCANCER;PANCAN",
            "status": 0,
            "importDate": "2018-04-10 00:00:00",
            "allSampleCount": 92,
            "sequencedSampleCount": 90,
            "cnaSampleCount": 90,
            "mrnaRnaSeqSampleCount": 79,
            "mrnaRnaSeqV2SampleCount": 0,
            "mrnaMicroarraySampleCount": 0,
            "methylationHm27SampleCount": 0,
            "miRnaSampleCount": 0,
            "rppaSampleCount": 0,
            "massSpectrometrySampleCount": 0,
            "svSampleCount": 0
        },
        {
            "studyId": "blca_tcga_pub",
            "name": "Bladder Urothelial Carcinoma (TCGA, Nature 2014)",
            "description": "Comprehensive molecular characterization of urothelial bladder carcinoma. Nat Genet 2014.",
            "publicStudy": True,
            "cancerTypeId": "blca",
            "referenceGenome": "hg19",
            "pmid": "24658044",
            "citation": "Rosenberg et al. Nat Genet 2014",
            "groups": "PANCAN",
            "status": 0,
            "importDate": "2014-05-15 00:00:00",
            "allSampleCount": 131,
            "sequencedSampleCount": 131,
            "cnaSampleCount": 130,
            "mrnaRnaSeqSampleCount": 0,
            "mrnaRnaSeqV2SampleCount": 0,
            "mrnaMicroarraySampleCount": 131,
            "methylationHm27SampleCount": 0,
            "miRnaSampleCount": 131,
            "rppaSampleCount": 0,
            "massSpectrometrySampleCount": 0,
            "svSampleCount": 0
        }
    ]
    
    # Configure the mock client's _make_api_request method
    # We need to be careful if other tests also mock _make_api_request. 
    # For simplicity here, we are directly setting it. 
    # In a larger test suite, consider using mocker.patch.object for more targeted mocking.
    # Mock the api_client.make_api_request for the first page call
    mock_api_request = AsyncMock(return_value=mock_studies_data)
    server_instance.api_client.make_api_request = mock_api_request # type: ignore

    response = await server_instance.get_cancer_studies(page_number=0, page_size=2)
    
    assert response == snapshot

@pytest.mark.asyncio
async def test_get_molecular_profiles_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from get_molecular_profiles matches the snapshot."""
    study_id_to_test = "acc_tcga"
    
    # Mock the API response for get_molecular_profiles
    mock_profiles_data = [
        {
            "molecularProfileId": "acc_tcga_rna_seq_v2_mrna",
            "studyId": "acc_tcga",
            "name": "mRNA expression (RNA Seq V2 RSEM)",
            "description": "mRNA expression from RNA Sequencing (version 2, RSEM normalized)",
            "molecularAlterationType": "MRNA_EXPRESSION",
            "datatype": "CONTINUOUS",
            "patientLevel": False,
            "genericAssayType": "MRNA_EXPRESSION",
            "showProfileInAnalysisTab": True,
            "sortOrder": 0
        },
        {
            "molecularProfileId": "acc_tcga_mutations",
            "studyId": "acc_tcga",
            "name": "Mutations",
            "description": "Somatic non-silent mutations from whole exome sequencing.",
            "molecularAlterationType": "MUTATION_EXTENDED",
            "datatype": "MAF",
            "patientLevel": False,
            "genericAssayType": "MUTATION",
            "showProfileInAnalysisTab": True,
            "sortOrder": 10
        }
    ]
    # Mock the api_client.make_api_request for the first page call
    mock_api_request = AsyncMock(return_value=mock_profiles_data)
    server_instance.api_client.make_api_request = mock_api_request # type: ignore

    response = await server_instance.get_molecular_profiles(study_id=study_id_to_test, page_number=0, page_size=2)
    
    assert response == snapshot

@pytest.mark.asyncio
async def test_get_cancer_types_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from get_cancer_types matches the snapshot."""
    # Mock the API response for get_cancer_types
    mock_cancer_types_data = [
        {
            "cancerTypeId": "acc",
            "name": "Adrenocortical Carcinoma",
            "dedicatedColor": "LightGreen",
            "shortName": "ACC",
            "parentCancerTypeId": "adrenal_gland"
        },
        {
            "cancerTypeId": "blca",
            "name": "Bladder Urothelial Carcinoma",
            "dedicatedColor": "Blue",
            "shortName": "BLCA",
            "parentCancerTypeId": "bladder"
        }
    ]
    # Mock the api_client.make_api_request for the first page call
    mock_api_request = AsyncMock(return_value=mock_cancer_types_data)
    server_instance.api_client.make_api_request = mock_api_request # type: ignore

    response = await server_instance.get_cancer_types(page_number=0, page_size=2)
    
    assert response == snapshot

@pytest.mark.asyncio
async def test_get_samples_in_study_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from get_samples_in_study matches the snapshot."""
    study_id_to_test = "acc_tcga"
    
    # Mock the API response for get_samples_in_study
    mock_samples_data = [
        {
            "sampleId": "TCGA-OR-A5J1-01",
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J1",
            "sampleType": "PRIMARY",
            "cancerType": "Adrenocortical Carcinoma"
        },
        {
            "sampleId": "TCGA-OR-A5J2-01",
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J2",
            "sampleType": "PRIMARY",
            "cancerType": "Adrenocortical Carcinoma"
        }
    ]
    # Mock the api_client.make_api_request for the first page call
    mock_api_request = AsyncMock(return_value=mock_samples_data)
    server_instance.api_client.make_api_request = mock_api_request # type: ignore

    response = await server_instance.get_samples_in_study(study_id=study_id_to_test, page_number=0, page_size=2)
    
    assert response == snapshot

@pytest.mark.asyncio
async def test_search_genes_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from search_genes matches the snapshot."""
    keyword_to_search = "BRCA"
    
    # Mock the API response for search_genes
    mock_genes_data = [
        {
            "entrezGeneId": 672,
            "hugoGeneSymbol": "BRCA1",
            "type": "protein-coding",
            "oncogene": False,
            "tumorSuppressor": True
        },
        {
            "entrezGeneId": 675,
            "hugoGeneSymbol": "BRCA2",
            "type": "protein-coding",
            "oncogene": False,
            "tumorSuppressor": True
        }
    ]
    # Mock the api_client.make_api_request for the first page call
    mock_api_request = AsyncMock(return_value=mock_genes_data)
    server_instance.api_client.make_api_request = mock_api_request # type: ignore

    response = await server_instance.search_genes(keyword=keyword_to_search, page_number=0, page_size=2)
    
    assert response == snapshot

@pytest.mark.asyncio
async def test_search_studies_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from search_studies matches the snapshot."""
    keyword_to_search = "PanCancer"
    
    # Mock the API response for search_studies
    mock_studies_search_data = [
        {
            "studyId": "acc_tcga",
            "name": "Adrenocortical Carcinoma (TCGA, PanCancer Atlas)",
            "description": "TCGA PanCanAtlas ACC",
            "publicStudy": True,
            "cancerTypeId": "acc",
            "referenceGenome": "hg19",
            "pmid": "29622464",
            "citation": "Cancer Genome Atlas Research Network. (2018). The Immune Landscape of Cancer. Immunity, 48(4).",
            "groups": "PANCANCER;PANCAN",
            "status": 0
        },
        {
            "studyId": "all_phase2_target_2018_pub",
            "name": "Acute Lymphoblastic Leukemia (TARGET, 2018)",
            "description": "TARGET ALL Phase 2. This study is part of the PanCancer Atlas project.",
            "publicStudy": True,
            "cancerTypeId": "all",
            "referenceGenome": "hg19",
            "pmid": "29622464",
            "citation": "Cancer Genome Atlas Research Network. (2018). The Immune Landscape of Cancer. Immunity, 48(4).",
            "groups": "PANCAN",
            "status": 0
        }
    ]
    
    mock_response_with_pagination = {
        "items": mock_studies_search_data,
        "pagination": {
            "page_number": 0,
            "page_size": 2,
            "total_items": 15, # Assuming 15 total matching studies for this mock
            "total_pages": 8,
            "sort_by": "studyId", # Typical sort for study searches
            "direction": "ASC",
            "has_more": True
        }
    }
    
    # Mock the _paginate_results helper method
    mock_paginate_request = AsyncMock(return_value=mock_response_with_pagination)
    server_instance._paginate_results = mock_paginate_request # type: ignore

    response = await server_instance.search_studies(keyword=keyword_to_search, page_number=0, page_size=2)
    
    assert response == snapshot

@pytest.mark.asyncio
async def test_get_mutations_in_gene_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from get_mutations_in_gene matches the snapshot."""
    study_id_to_test = "acc_tcga"
    sample_list_id_to_test = "acc_tcga_all" # This is often studyId + suffix like _all, _cnaseq, _sequenced
    gene_id_to_test = "TP53"
    # page_number and page_size will use defaults (0 and 50)

    # Mock data for the first API call (to fetch molecular profiles for the study)
    mock_molecular_profiles_list = [
        {
            "molecularProfileId": "acc_tcga_rna_seq_v2_mrna",
            "studyId": "acc_tcga",
            "name": "mRNA expression (RNA Seq V2 RSEM)",
            "molecularAlterationType": "MRNA_EXPRESSION",
            "datatype": "CONTINUOUS",
            "showProfileInAnalysisTab": True
        },
        {
            "molecularProfileId": "acc_tcga_mutations", # This is the one the method should find and use
            "studyId": "acc_tcga",
            "name": "Mutations",
            "molecularAlterationType": "MUTATION_EXTENDED",
            "datatype": "MAF",
            "showProfileInAnalysisTab": True
        },
        {
            "molecularProfileId": "acc_tcga_cna",
            "studyId": "acc_tcga",
            "name": "Copy Number Alterations",
            "molecularAlterationType": "COPY_NUMBER_ALTERATION",
            "datatype": "DISCRETE",
            "showProfileInAnalysisTab": True
        }
    ]

    # Mock data for the second API call (to fetch mutations for the identified molecular profile)
    mock_mutations_data = [
        {
            "uniqueSampleKey": "TCGA-OR-A5J1-01:acc_tcga_mutations",
            "uniquePatientKey": "TCGA-OR-A5J1:acc_tcga_mutations",
            "molecularProfileId": "acc_tcga_mutations",
            "sampleId": "TCGA-OR-A5J1-01",
            "patientId": "TCGA-OR-A5J1",
            "entrezGeneId": 7157,
            "hugoGeneSymbol": "TP53",
            "mutationStatus": "SOMATIC",
            "mutationType": "Missense_Mutation",
            "aminoAcidChange": "R248W",
            "chromosome": "17",
            "startPosition": 7577538,
            "endPosition": 7577538,
            "referenceAllele": "C",
            "variantAllele": "T",
            "proteinPosStart": 248,
            "proteinPosEnd": 248,
            "keyword": "TP53 Missense_Mutation R248W"
        },
        {
            "uniqueSampleKey": "TCGA-OR-A5J2-01:acc_tcga_mutations",
            "uniquePatientKey": "TCGA-OR-A5J2:acc_tcga_mutations",
            "molecularProfileId": "acc_tcga_mutations",
            "sampleId": "TCGA-OR-A5J2-01",
            "patientId": "TCGA-OR-A5J2",
            "entrezGeneId": 7157,
            "hugoGeneSymbol": "TP53",
            "mutationStatus": "SOMATIC",
            "mutationType": "Nonsense_Mutation",
            "aminoAcidChange": "Q136*",
            "chromosome": "17",
            "startPosition": 7578459,
            "endPosition": 7578459,
            "referenceAllele": "C",
            "variantAllele": "T",
            "proteinPosStart": 136,
            "proteinPosEnd": 136,
            "keyword": "TP53 Nonsense_Mutation Q136*"
        }
    ]

    # Mock the _make_api_request method to return different values on subsequent calls
    mock_api_call = AsyncMock(side_effect=[mock_molecular_profiles_list, mock_mutations_data])
    server_instance.api_client.make_api_request = mock_api_call # type: ignore

    response = await server_instance.get_mutations_in_gene(
        study_id=study_id_to_test,
        sample_list_id=sample_list_id_to_test,
        gene_id=gene_id_to_test
        # Using default page_number, page_size, etc.
    )

    assert response == snapshot

@pytest.mark.asyncio
async def test_get_clinical_data_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from get_clinical_data matches the snapshot (fetching all attributes)."""
    study_id_to_test = "acc_tcga"
    # No sample_list_id or attribute_ids needed for this test case (fetches all patient data)

    # Mock the API response for get_clinical_data (when fetching all for a study)
    # This endpoint (studies/{study_id}/clinical-data) returns a flat list of clinical data items.
    # The get_clinical_data method then processes this into a nested structure by patient.
    mock_flat_clinical_data_from_api = [
        {
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J1",
            "sampleId": "TCGA-OR-A5J1-01", # Sample ID might still be present in raw data
            "clinicalAttributeId": "AGE",
            "value": "50"
        },
        {
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J1",
            "sampleId": "TCGA-OR-A5J1-01",
            "clinicalAttributeId": "SEX",
            "value": "Female"
        },
        {
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J2",
            "sampleId": "TCGA-OR-A5J2-01",
            "clinicalAttributeId": "AGE",
            "value": "65"
        },
        {
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J2",
            "sampleId": "TCGA-OR-A5J2-01",
            "clinicalAttributeId": "SEX",
            "value": "Male"
        },
        {
            "studyId": "acc_tcga", # Test a third patient with one attribute
            "patientId": "TCGA-OR-A5J3",
            "sampleId": "TCGA-OR-A5J3-01",
            "clinicalAttributeId": "AJCC_PATHOLOGIC_TUMOR_STAGE",
            "value": "STAGE I"
        }
    ]

    # Mock the _make_api_request method as get_clinical_data calls it directly
    mock_api_call = AsyncMock(return_value=mock_flat_clinical_data_from_api)
    server_instance.api_client.make_api_request = mock_api_call # type: ignore

    response = await server_instance.get_clinical_data(
        study_id=study_id_to_test
        # Using default page_number, page_size, attribute_ids=None etc.
    )

    assert response == snapshot

@pytest.mark.asyncio
async def test_get_clinical_data_specific_attributes_snapshot(server_instance: CBioPortalMCPServer, snapshot: SnapshotAssertion, mocker):
    """Test that the response from get_clinical_data matches the snapshot when specific attributes are requested."""
    study_id_to_test = "acc_tcga"
    attribute_ids_to_test = ["AGE", "SEX"]

    # Mock the API response for get_clinical_data/fetch (POST request)
    # This endpoint should return a flat list of clinical data items for the requested attributes.
    # The server method will then process this into a nested structure by patient.
    mock_flat_clinical_data_from_api_specific = [
        {
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J1",
            "sampleId": "TCGA-OR-A5J1-01",
            "clinicalAttributeId": "AGE",
            "value": "50"
        },
        {
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J1",
            "sampleId": "TCGA-OR-A5J1-01",
            "clinicalAttributeId": "SEX",
            "value": "Female"
        },
        {
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J2",
            "sampleId": "TCGA-OR-A5J2-01",
            "clinicalAttributeId": "AGE",
            "value": "65"
        },
        {
            "studyId": "acc_tcga",
            "patientId": "TCGA-OR-A5J2",
            "sampleId": "TCGA-OR-A5J2-01",
            "clinicalAttributeId": "SEX",
            "value": "Male"
        }
        # Note: We are only returning data for AGE and SEX, as requested.
        # A patient like TCGA-OR-A5J3 who only had AJCC_PATHOLOGIC_TUMOR_STAGE in the previous test
        # would not appear here unless that attribute was also requested and returned by the mock.
    ]

    # Mock the _make_api_request method
    mock_api_call = AsyncMock(return_value=mock_flat_clinical_data_from_api_specific)
    server_instance.api_client.make_api_request = mock_api_call # type: ignore

    response = await server_instance.get_clinical_data(
        study_id=study_id_to_test,
        attribute_ids=attribute_ids_to_test
        # Using default page_number, page_size, etc.
    )

    # Assert that _make_api_request was called correctly for the /fetch endpoint
    expected_endpoint = f"studies/{study_id_to_test}/clinical-data/fetch"
    expected_payload = {"attributeIds": attribute_ids_to_test, "clinicalDataType": "PATIENT"}
    # Default params for pagination are pageNumber=0, pageSize=50, direction="ASC", clinicalDataType="PATIENT"
    # The clinicalDataType in the payload for /fetch is separate from query params if any.
    expected_api_call_params = {
        "pageNumber": 0, 
        "pageSize": 50, 
        "direction": "ASC", 
        "clinicalDataType": "PATIENT"
    }

    mock_api_call.assert_called_once_with(
        expected_endpoint,
        method="POST",
        params=expected_api_call_params, # Check if these are the correct default query params
        json_data=expected_payload
    )

    assert response == snapshot

@pytest.mark.asyncio
async def test_get_gene_panels_for_study_snapshot(server_instance, snapshot, mocker):
    """Test snapshot for get_gene_panels_for_study method."""
    study_id = "acc_tcga"
    mock_response = [
        {
            "genePanelId": "IMPACT341",
            "name": "MSK-IMPACT Clinical Sequencing Cohort (MSK, Nat Med 2017)",
            "description": "341 cancer-associated genes",
            "genes": [
                {"entrezGeneId": 1, "hugoGeneSymbol": "GENE1"},
                {"entrezGeneId": 2, "hugoGeneSymbol": "GENE2"}
            ]
        },
        {
            "genePanelId": "PEDS-IMPACT",
            "name": "MSK-IMPACT Pediatric Panel",
            "description": "Pediatric panel of genes",
            "genes": [
                {"entrezGeneId": 3, "hugoGeneSymbol": "GENE3"},
                {"entrezGeneId": 4, "hugoGeneSymbol": "P53_MUTANT"} # Example with specific variant
            ]
        }
    ]

    # Mock the _make_api_request method
    mocker.patch.object(
        server_instance.api_client,
        'make_api_request',
        return_value=mock_response
    )

    # Call the method under test
    result = await server_instance.get_gene_panels_for_study(study_id=study_id, page_size=2) # Fetch one page

    # Assert the result against the snapshot
    assert result == snapshot

@pytest.mark.asyncio
async def test_get_gene_panel_details_snapshot(server_instance, snapshot, mocker):
    """Test snapshot for get_gene_panel_details method."""
    gene_panel_id = "IMPACT468"
    mock_response = [
        {
            "genePanelId": "IMPACT468",
            "name": "MSK-IMPACT Clinical Sequencing Cohort (MSK, Cancer Cell 2015)",
            "description": "468 key cancer genes",
            "genes": [
                {"entrezGeneId": 7157, "hugoGeneSymbol": "TP53"},
                {"entrezGeneId": 207, "hugoGeneSymbol": "AKT1"},
                {"entrezGeneId": 595, "hugoGeneSymbol": "CCND1"}
            ]
        }
    ]

    # Mock the _make_api_request method
    mocker.patch.object(
        server_instance.api_client,
        'make_api_request',
        return_value=mock_response
    )

    # Call the method under test
    # The method itself expects to get a list from _make_api_request and will extract the first element
    result = await server_instance.get_gene_panel_details(gene_panel_id=gene_panel_id, projection="DETAILED")

    # Assert the result against the snapshot
    assert result == snapshot

