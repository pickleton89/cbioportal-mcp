import pytest
import sys
import os

# Add the parent directory to the path so we can import the cbioportal_server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cbioportal_server import CBioPortalMCPServer

@pytest.fixture(scope="session")
def cbioportal_server_instance():
    """Provides a CBioPortalMCPServer instance for tests."""
    return CBioPortalMCPServer(base_url="https://www.cbioportal.org/api", client_timeout=30.0)

@pytest.fixture(scope="session")
def mock_studies_data():
    """Provides mock study data."""
    return [
        {"studyId": f"study_{i}", "name": f"Study {i}", "description": f"Description {i}"} 
        for i in range(1, 101)
    ]

@pytest.fixture(scope="session")
def mock_cancer_types_data():
    """Provides mock cancer type data."""
    return [
        {"cancerTypeId": f"type_{i}", "name": f"Cancer Type {i}"} 
        for i in range(1, 51)
    ]

@pytest.fixture(scope="session")
def mock_samples_data():
    """Provides mock sample data."""
    return [
        {"sampleId": f"sample_{i}", "patientId": f"patient_{i % 20}", "studyId": "study_1"} 
        for i in range(1, 201)
    ]

@pytest.fixture(scope="session")
def mock_genes_data():
    """Provides mock gene data."""
    return [
        {"entrezGeneId": i, "hugoGeneSymbol": f"GENE{i}", "type": "protein-coding"} 
        for i in range(1, 31)
    ]

@pytest.fixture(scope="session")
def mock_mutations_data():
    """Provides mock mutation data."""
    return [
        {
            "uniqueSampleKey": f"sample_{i}:study_mut",
            "uniquePatientKey": f"patient_{i%20}:study_mut",
            "molecularProfileId": "mutation_profile_1",
            "sampleId": f"sample_{i}",
            "patientId": f"patient_{i%20}",
            "studyId": "study_mut",
            "gene": {"hugoGeneSymbol": "TP53", "entrezGeneId": 7157, "ncbiBuild": "37"},
            "chromosome": "17",
            "startPosition": 7577098 + i,
            "endPosition": 7577098 + i,
            "proteinChange": f"R{175+i}H",
            "mutationStatus": "SOMATIC",
            "mutationType": "Missense_Mutation",
            "keyword": f"TP53_MUT_{i}" # Example field for sorting
        } for i in range(1, 76) # 75 mock mutations
    ]

@pytest.fixture(scope="session")
def mock_clinical_data_data():
    """Provides mock clinical data."""
    clinical_data = [
        {
            "uniqueSampleKey": f"sample_{i}:study_clin",
            "uniquePatientKey": f"patient_{i // 2}:study_clin",
            "sampleId": f"sample_{i}",
            "patientId": f"patient_{i // 2}",
            "studyId": "study_clin",
            "attributeId": "AGE_AT_DIAGNOSIS",
            "value": str(40 + i) 
        } for i in range(1, 81) # 80 mock clinical data entries
    ]
    # Add some SEX data for testing attribute_ids variety
    for idx in range(0, len(clinical_data)):
        if idx % 3 == 0:
            clinical_data[idx]["attributeId"] = "SEX"
            clinical_data[idx]["value"] = "Female" if idx % 2 == 0 else "Male"
    return clinical_data

@pytest.fixture
def mock_study_data():
    """Mock data for a single study."""
    return {
        "studyId": "study_1",
        "name": "Test Study",
        "description": "A study for testing",
        "publicStudy": True,
        "cancerTypeId": "mixed",
    }

@pytest.fixture
def mock_gene_data():
    """Mock data for a single gene."""
    return {"entrezGeneId": 672, "hugoGeneSymbol": "BRCA1", "type": "protein-coding"}

@pytest.fixture
def mock_study_detail_brca():
    return {
        "studyId": "brca_tcga",
        "name": "BRCA TCGA",
        "description": "Breast Cancer TCGA",
    }

@pytest.fixture
def mock_study_detail_luad():
    return {
        "studyId": "luad_tcga",
        "name": "LUAD TCGA",
        "description": "Lung Adenocarcinoma TCGA",
    }

@pytest.fixture
def mock_gene_detail_tp53():
    return {"entrezGeneId": 7157, "hugoGeneSymbol": "TP53", "type": "protein-coding"}

@pytest.fixture
def mock_gene_detail_brca1():
    return {"entrezGeneId": 672, "hugoGeneSymbol": "BRCA1", "type": "protein-coding"}

@pytest.fixture
def mock_gene_batch_response_page1():
    return [
        {"entrezGeneId": 7157, "hugoGeneSymbol": "TP53", "type": "protein-coding"},
        {"entrezGeneId": 672, "hugoGeneSymbol": "BRCA1", "type": "protein-coding"},
    ]

@pytest.fixture
async def cbioportal_server_instance_unstarted():
    """Provides a CBioPortalMCPServer instance without calling startup/shutdown."""
    # Ensure CBioPortalMCPServer is imported; it should be from the top of conftest.py
    server = CBioPortalMCPServer(base_url="http://mocked.cbioportal.org/api", client_timeout=30.0)
    yield server
    # No automatic startup/shutdown here, tests will manage if needed.
    # If a test using this fixture calls server.startup(), it should handle shutdown if necessary,
    # or rely on test isolation if client state doesn't persist or conflict.
