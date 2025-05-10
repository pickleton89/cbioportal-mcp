# Changelog

All notable changes to the cBioPortal MCP Server project will be documented in this file.

## [Unreleased]



### 2025-05-09

#### Session Summary (2025-05-09 13:52)

- **Pagination Implementation Completion**:
  - Completed pagination support for the two remaining collection-returning methods:
    - `get_mutations_in_gene`: Added pagination parameters and updated implementation to properly handle pagination
    - `get_clinical_data`: Added pagination parameters and updated implementation to support pagination for both GET and POST requests
  - Ensured consistent pagination interface across all methods with the same parameter names and response structure
  - Updated method documentation with detailed parameter descriptions and return value documentation
  - Maintained special handling for `limit=0` (fetch all results) in the newly updated methods

- **API Documentation Review**:
  - Reviewed the cBioPortal API v3 documentation (OpenAPI 3.1.0) to ensure proper implementation
  - Confirmed the available pagination parameters and their usage across different endpoints
  - Verified the correct endpoint paths and parameter structures for mutation and clinical data endpoints

- **MCP Integration Research**:
  - Explored the Model Context Protocol (MCP) documentation and Python SDK
  - Gained familiarity with MCP server implementation patterns for future enhancements
  - Reviewed how the cBioPortal server exposes API functionality through MCP tools

- **Code Quality Improvements**:
  - Fixed docstring syntax error in the `run` method
  - Addressed critical syntax issues to ensure proper code execution
  - Maintained consistent code style across the newly implemented pagination methods

#### Pagination Completion

- **Milestone**: Pagination support has been fully implemented and verified across all collection-returning API methods in the server.
  - All relevant methods now accept `page_number`, `page_size`, `sort_by`, `direction`, and `limit` parameters.
  - Each method returns a response with a `pagination` metadata dictionary for consistent client consumption.
  - Special handling for `limit=0` (fetch all results) is in place where supported by the API.
  - Methods covered:
    - `get_cancer_studies`
    - `get_cancer_types`
    - `get_samples_in_study`
    - `search_genes`
    - `search_studies`
    - `get_molecular_profiles`
    - `get_mutations_in_gene`
    - `get_clinical_data`

- **Quality Improvements**:
  - Audited all endpoints to ensure no collection-returning method is missing pagination support.
  - Standardized error handling and response formatting for paginated endpoints.

#### Testing Results

- **Test Execution**:
  - Successfully passed 11 of 11 tests after all implementation fixes
  - Verified proper pagination functionality across all methods
  - Confirmed batch processing for gene retrieval works correctly
  - Addressed code linting issues for better quality and maintainability

#### Implementation Fixes

- **Pagination Implementation**:
  - Fixed `get_cancer_studies` method to properly use pagination parameters
  - Updated `search_genes` method to use correct endpoint with pagination
  - Ensured consistent pagination structure across all methods
  - Implemented special case handling for "all results" (limit=0) requests
  - Added proper limit handling to truncate results when needed

- **Method Implementation Updates**:
  - Updated `get_genes` to use batch endpoint for better efficiency
  - Simplified `get_study_details` to focus on core functionality
  - Improved code quality by fixing lint issues

#### Testing Infrastructure

- **Testing Framework Setup**:
  - Added pytest configuration with pytest.ini
  - Created comprehensive unit test structure with mocking
  - Added test coverage reporting capability with pytest-cov
  
- **Test Files Implementation**:
  - Created test_pagination.py with specific tests for pagination features
  - Created test_cbioportal_server.py for basic functionality tests
  - Added tests for error handling and configuration

- **Dependency Updates**:
  - Added pytest and pytest-cov to requirements.txt
  - Updated MCP library version constraint to use available versions (1.0.0-1.8.0)
  
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

#### Bug Fixes (Post-Pagination Implementation)

- **Server-Side Logic (`cbioportal_server.py`)**:
  - Corrected the API endpoint in the `search_genes` method from `genes/search` to the standard `genes` endpoint. This resolves an issue where tests for gene searching were failing due to an incorrect API path.
  - Revised the `has_more` pagination flag calculation in the following methods to accurately reflect whether more data might be available from the API, rather than relying on the count of items on the current page:
    - `get_cancer_studies`
    - `get_cancer_types`
    - `get_samples_in_study`
    - `search_genes`
    - `get_mutations_in_gene`
    - `get_clinical_data`
  - This change fixes previous assertion errors in tests where the `has_more` flag was incorrectly `False` when subsequent pages were expected.

#### Code Improvements & Linting

- **Code Health in `cbioportal_server.py`**:
  - Removed unused Python imports (`json`, `os`, `dotenv.load_dotenv`) to clean up the codebase.
  - Refactored error message string formatting:
    - Converted f-strings to regular strings in instances where placeholders were not actually used, addressing lint warnings.
    - Ensured that `study_id` (and other relevant variables) are correctly included in error messages for methods like `get_mutations_in_gene`, `get_clinical_data`, and `get_study_details` by using f-strings appropriately. This restores clarity to error messages that were inadvertently made generic.

### 2025-05-09 (16:00)

#### Pagination Logic Completion and Testing

- **Test Suite Fixes**:
  - Fixed test failures related to multiple API calls in `get_mutations_in_gene` by:
    - Updating tests to use `assert_has_calls()` instead of `assert_called_with()`
    - Correctly mocking both the molecular profiles request and the mutations request in sequence
    - Adding proper side effect patterns for mock API responses in sequence
  - Fixed test failures in `get_clinical_data` tests by:
    - Accounting for the patient-centric data structure where multiple clinical data entries are consolidated per patient
    - Updating response validation to correctly check unique patient counts instead of raw data counts
    - Adding proper test cases for both GET and POST API request paths

- **API Response Consistency**:
  - Modified the `get_clinical_data` method to calculate `total_found` based on the number of unique patients rather than raw clinical data entries
  - This ensures the pagination metadata accurately reflects the actual data returned to clients
  - Improved test assertions to verify that pagination structure is consistent with the response content

- **Dependency Management**:
  - Added `fastmcp>=0.1.0` to `requirements.txt` to support server functionality
  - Updated project to properly use the latest fastmcp package for MCP server implementation

- **Code Architecture Improvements**:
  - Ensured all tests correctly model the internal behavior of methods that make multiple API calls
  - Improved mock setup to better simulate the actual API responses
  - Added better test documentation to explain the data transformation from raw API responses to structured client data

#### Validation Results

- **Test Status**:
  - Successfully completed all 15 tests with no failures or errors
  - Confirmed proper pagination behavior for all collection-returning methods
  - Verified correct API endpoint usage for all methods
  - Ensured the `has_more` flag correctly indicates when additional pages of data might be available



### 2025-05-09 (17:43)

#### Async Implementation for Performance Enhancement

- **Step 1: Replace HTTP Client**:
  - Replaced `requests` with `httpx` for async HTTP support
  - Added `asyncio` import for asynchronous programming capabilities
  - This change is the foundation for converting synchronous API calls to asynchronous

- **Step 2: Create Async Client Manager**:
  - Implemented async lifecycle management with `startup` and `shutdown` hooks
  - Added `httpx.AsyncClient` initialization in the startup process
  - Configured proper client cleanup on server shutdown
  - Registered FastMCP lifecycle hooks using `mcp.on_startup` and `mcp.on_shutdown`

- **Step 3: Convert API Methods to Async**:
  - Transformed `_make_api_request` helper method to async with proper error handling
  - Converted `get_cancer_studies` method to use async/await pattern
  - Added await keyword to API calls where needed
  - Maintained the same method signature and response structure for compatibility

- **Step 4: Implement Pagination with Async Generators**:
  - Created `paginate_results` async generator for efficient paging through API results
  - Added `collect_all_results` helper to gather complete datasets when needed
  - Enhanced `get_cancer_studies` to use new pagination infrastructure
  - Made `run` method async to support full async lifecycle
  - Updated main function with better documentation and enhanced CLI options

- **Step 5: Update Run Logic**:
  - Added comprehensive logging system with configurable levels
  - Implemented proper signal handling for graceful shutdowns
  - Enhanced error reporting with structured logging
  - Added startup and shutdown status reporting
  - Improved CLI interface with better argument documentation

- **Step 6: Update Tool Registration for Async Methods**:
  - Converted remaining methods to async (`get_cancer_types`, `get_genes`, `get_study_details`)
  - Enhanced `get_cancer_types` to use the async pagination infrastructure
  - Added detailed method descriptions to tool registrations
  - Categorized tools by functionality (data retrieval, molecular data)
  - Added thorough documentation on how FastMCP handles async methods

- **Step 7: Implement Concurrency for Bulk Operations**:
  - Added `get_multiple_studies` method to fetch studies in parallel using `asyncio.gather`
  - Implemented `get_multiple_genes` with smart batching for efficient concurrent requests
  - Added performance metrics like execution time to concurrent operations
  - Registered new bulk operations as MCP tools with descriptive documentation
  - Resolved the unused `asyncio` import warning by leveraging asyncio's concurrency features

### 2025-05-09 (18:04)

#### Bug Fix: Method Registration Error

- **Issue**: During testing, discovered a reference to a non-existent method `get_mutations_by_gene_and_study` in the tool registration code
- **Resolution**: Removed the invalid tool registration line from `_register_tools` method
- **Impact**: This fix enables the server to start properly without throwing an `AttributeError`
- **Root Cause**: The method was likely referenced during development but never implemented, or was removed without updating the registration code

#### FastMCP Compatibility Fix

- **Issue**: The installed version of FastMCP doesn't support the `on_startup` and `on_shutdown` lifecycle hooks
- **Resolution**: Modified the server initialization to directly create the HTTP client instead of using lifecycle hooks
- **Impact**: Ensures compatibility with the available FastMCP version
- **Adaptation**: Updated test script to remove calls to startup/shutdown methods that are no longer needed

#### Performance Testing Results

- **Test Implementation**: Created a test script (`test_async.py`) to benchmark async vs sequential operations
- **Sequential vs Concurrent Study Fetching**:
  - Sequential fetching: 1.31 seconds to fetch 10 studies
  - Concurrent fetching: 0.29 seconds for the same operation
  - **4.57x performance improvement** with the async implementation
  - Data consistency verified between both approaches
- **Gene Batch Concurrency**:
  - Successfully fetched 14 genes in 0.26 seconds with automatic batching
  - Demonstrated the effective batch processing with concurrent execution
- **Validation**: All operations produced consistent results with excellent performance gains


### 2025-05-10 (09:00)

#### Async Implementation Completion

- **Fixed Async Methods and Tests**:
  - Completed the transition to fully async implementation, fixing the remaining issues with coroutines and tests
  - Added `await` to the second API call in `get_mutations_in_gene` method to ensure proper handling of asynchronous operations
  - Converted `get_clinical_data` method to be async and added `await` to its API calls
  - Updated all tests to properly handle async functions using `asyncio.run()`
  - Fixed tests that were getting stuck in infinite loops by improving async mock handling
  - Fixed all remaining test failures with proper async mocking patterns

- **Test Suite Results**:
  - All 15 tests now pass successfully
  - Fixed specific test issues in:
    - `test_get_mutations_in_gene_pagination`
    - `test_get_mutations_in_gene_with_sort_and_limit`
    - `test_get_clinical_data_pagination`
    - `test_get_clinical_data_with_sort_and_limit`
    - `test_get_all_results`

- **Code Quality**:
  - Improved mock setup for async methods using async side_effect functions
  - Standardized approach to testing asynchronous API methods
  - Eliminated coroutine handling errors and RuntimeWarnings


#### FastMCP Async Lifecycle Management Fix (09:30)

- **Fixed Server Startup and Lifecycle Management**:
  - Modified the server's run method to be synchronous, which matches FastMCP's expected pattern
  - Properly registered async lifecycle hooks via `mcp.on_startup` and `mcp.on_shutdown` properties
  - Simplified the main function to let FastMCP handle the event loop internally
  - Fixed integration with Claude Desktop which now successfully connects to the server
  - Maintained the benefits of async implementation for I/O-bound API calls

### 2025-05-10 (09:42)

#### Async Function Call Fixes

- **Resolved `TypeError: 'coroutine' object is not iterable` in `search_studies`**:
  - Modified `search_studies` to be an `async def` function.
  - Ensured the call to `self._make_api_request("studies")` within `search_studies` is properly `await`ed.
  - Improved error handling within `search_studies` for API and network issues.
  - Adjusted pagination logic in the response when `limit` is 0 for better clarity.
- **Proactively fixed `get_molecular_profiles`**:
  - Modified `get_molecular_profiles` to be an `async def` function.
  - Ensured the call to `self._make_api_request(...)` within `get_molecular_profiles` is properly `await`ed.
- **Impact**: These changes resolve runtime errors when these functions are called, allowing them to correctly interact with the asynchronous `_make_api_request` method. This enhances the stability and reliability of the MCP server when performing these operations.

### 2025-05-10 (10:23)

#### Test Code Refinement
- Refactored `test_get_cancer_studies_pagination` in `tests/test_pagination.py` to use `pytest.mark.parametrize`. This consolidates multiple test scenarios into a single, data-driven test function, improving conciseness and maintainability.

#### Server Core & Lifecycle Management
- Corrected `CBioPortalMCPServer.__init__` to defer `httpx.AsyncClient` initialization to the `startup` method, preventing redundant client creation.
- Ensured `startup` and `shutdown` methods are correctly assigned to `FastMCP` instance's `on_startup` and `on_shutdown` lifecycle hooks.
- Added tests to `tests/test_cbioportal_server.py` to verify:
  - Correct registration of `startup` and `shutdown` lifecycle hooks.
  - `startup` method initializes `httpx.AsyncClient` as expected.
  - `shutdown` method calls `aclose()` on the active client.
- Refined `main()` function in `cbioportal_server.py` for clarity and robust `stdio` transport handling, removing prior experimental WebSocket code and addressing associated lint errors.
- Fixed various import-related lint issues in `cbioportal_server.py`.

#### Test Suite Modernization

- **Initiated `pytest` Migration**:
  - Added `pytest-asyncio` to project dependencies (`requirements.txt`) to support asynchronous testing with `pytest`.
  - Successfully converted `tests/test_cbioportal_server.py` from `unittest` to `pytest` style:
    - Replaced `unittest.TestCase` structure with standalone test functions.
    - Converted `setUp` method and mock data initialization to `pytest` fixtures (`mock_study_data`, `mock_gene_data`, `cbioportal_server_instance`).
    - Updated assertion syntax from `self.assertEqual` etc., to standard Python `assert`.
    - Adapted asynchronous tests using `@pytest.mark.asyncio` and `await`, removing the need for `asyncio.run()` within tests.
  - Configured `pytest.ini` to include `asyncio_mode = auto` and `asyncio_default_fixture_loop_scope = function` to address `pytest-asyncio` deprecation warnings and improve integration.
- **Impact**: This modernization effort aims to make the test suite more readable, maintainable, and aligned with current Python testing best practices. The `tests/test_cbioportal_server.py` file now fully utilizes `pytest` features.

#### Next Steps

- The cBioPortal MCP server now features full async support with significant performance improvements
- Potential future enhancements:
  - Apply concurrent fetching to remaining collection methods that could benefit from parallelization
  - Implement more sophisticated error handling and retry mechanisms for network errors
  - Add configuration options for controlling concurrency limits and timeout settings
  - Develop more comprehensive benchmarking and performance monitoring tools
  - Consider caching frequently requested data to further improve performance

### 2025-05-10 (11:00)

#### Server Lifecycle and Tool Registration Enhancements

- **Server Core Refinements (`cbioportal_server.py`)**:
  - Refactored `CBioPortalMCPServer.__init__` to correctly initialize `httpx.AsyncClient` within the `startup` method, preventing client initialization issues.
  - Ensured `startup` and `shutdown` async methods are properly registered as lifecycle hooks directly on the `FastMCP` instance (using `mcp.on_startup` and `mcp.on_shutdown`).
  - Removed the redundant `run()` method from `CBioPortalMCPServer` as its functionality is managed by `FastMCP`.
  - Simplified the `main()` function for improved clarity and robust `stdio` transport handling.
- **Test Suite Enhancements (`tests/test_cbioportal_server.py`)**:
  - Added comprehensive tests for server lifecycle management:
    - `test_lifecycle_hooks_registered`: Verifies correct registration of startup/shutdown hooks.
    - `test_startup_initializes_client`: Confirms HTTP client initialization on startup.
    - `test_shutdown_closes_client`: Ensures HTTP client is closed on shutdown.
  - Implemented `test_tool_registration` to dynamically verify that all intended public API methods are registered as MCP tools and that the list of registered tools is accurate.
    - Iteratively debugged tool fetching logic, adapting to the correct `FastMCP.get_tools()` method.
    - Corrected test logic to handle `mcp.get_tools()` returning a list of tool name strings directly.
    - Synchronized the `expected_tools` set with the actual public methods in `CBioPortalMCPServer`, removing entries for non-existent methods (`get_clinical_attributes_in_study`, `get_all_clinical_attributes`) to ensure test accuracy.
- **Impact**: These changes significantly improve the robustness and maintainability of the server's core lifecycle management and tool registration processes. The enhanced test suite now provides strong guarantees for these critical functionalities, ensuring all exposed tools are correctly registered and lifecycle events are handled as expected.

#### Pagination Test Suite Enhancements (11:08)

- **Granular Tests for `paginate_results` (`tests/test_pagination.py`)**:
  - Added comprehensive unit tests for the `paginate_results` helper method in `cbioportal_server.py` to cover various scenarios:
    - `test_paginate_results_basic`: Verifies basic multi-page iteration.
    - `test_paginate_results_empty_first_call`: Ensures correct handling when the API returns no data on the first call.
    - `test_paginate_results_with_max_pages`: Confirms that the `max_pages` parameter correctly limits fetched pages.
    - `test_paginate_results_last_page_partial`: Checks correct termination when the API's last page has fewer items than `page_size`.
- **Bug Fix in `paginate_results` (`cbioportal_server.py`)**:
  - Corrected an issue where `unittest.mock.call` would not accurately capture `params` for `_make_api_request` due to mutable dictionary references.
  - Fixed by passing `request_params.copy()` to `_make_api_request`, ensuring each call receives a distinct snapshot of parameters.
- **Impact**: Improved test coverage for the core pagination logic, leading to increased confidence in data retrieval. The bug fix ensures test accuracy for methods relying on `paginate_results`.

#### Next Steps

- The cBioPortal MCP server now features full async support with significant performance improvements
- Potential future enhancements:
  - Apply concurrent fetching to remaining collection methods that could benefit from parallelization
  - Implement more sophisticated error handling and retry mechanisms for network errors
  - Add configuration options for controlling concurrency limits and timeout settings
  - Develop more comprehensive benchmarking and performance monitoring tools
  - Consider caching frequently requested data to further improve performance