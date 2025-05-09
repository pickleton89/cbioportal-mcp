# Changelog

All notable changes to the cBioPortal MCP Server project will be documented in this file.

## [Unreleased]

### 2025-05-09

#### Project Setup and Initial Implementation

- **Repository Initialization**: Created a Git repository for version control and collaboration
- **Documentation**: 
  - Created comprehensive README.md with installation instructions, usage examples, and feature documentation
  - Added LICENSE file with MIT License
  - Created requirements.txt file specifying dependencies
  - Added standard .gitignore file for Python projects

#### API Research and Evaluation

- **API Documentation Review**: 
  - Analyzed cBioPortal API v2 Swagger documentation
  - Discovered and explored cBioPortal API v3 (OpenAPI 3.1.0) documentation
  - Documented differences between v2 and v3 APIs
  - Identified key endpoints and patterns for data retrieval

#### Code Improvements

- **Pagination Support**: Added LLM-optimized pagination to collection-based methods:
  - `get_cancer_studies`: Added pagination, sorting, and limit parameters
  - `get_cancer_types`: Added pagination, sorting, and limit parameters
  - `get_samples_in_study`: Added pagination, sorting, and limit parameters
  - `search_genes`: Added pagination, sorting, and limit parameters
  
- **Response Structure Optimization**:
  - Restructured method responses for better LLM interaction
  - Added consistent pagination metadata across methods
  - Implemented `has_more` flag for easier pagination state tracking
  
- **Method Parameter Enhancements**:
  - Added `gene_id_type` and `projection` parameters to `get_genes`
  - Improved method documentation with detailed parameter descriptions
  - Added explanations of valid values for enumeration parameters

#### LLM Interaction Optimizations

- **Context Window Management**: Set conservative default page sizes (50 items)
- **Progressive Information Retrieval**: Added `limit` parameter to control total results
- **Explicit Documentation**: Added detailed comments explaining valid sort fields for each method