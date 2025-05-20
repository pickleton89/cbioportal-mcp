# cBioPortal MCP Server Refactoring Plan

> **Current State (2025-05-20)**: The project has made significant progress with testing (92 passing tests) and some refactoring. This plan has been updated to reflect the current state and guide the remaining refactoring work.

## 1. Project Structure
```
cbioportal_mcp/
├── __init__.py
├── api_client.py         # HTTP client and request handling
├── endpoints/            # API endpoint handlers
│   ├── __init__.py
│   ├── studies.py
│   ├── genes.py
│   ├── samples.py
│   ├── molecular_profiles.py
│   └── gene_panels.py
├── models.py             # Data models and schemas
├── utils/                # Utility functions
│   ├── __init__.py
│   ├── pagination.py
│   └── validation.py
└── server.py            # Main server class and MCP integration
```

## 2. Phase 1: Core Components (Day 1-2)

### 2.1. API Client (`api_client.py`)
- [ ] Create `APIClient` class
- [ ] Move `_make_api_request` logic
- [ ] Add retry mechanism
- [ ] Implement request/response logging

### 2.2. Utilities (`utils/`)
- [ ] `pagination.py`: Move pagination logic
- [ ] `validation.py`: Input validation helpers
- [ ] `logging.py`: Centralized logging setup

## 3. Phase 2: Endpoint Modules (Day 3-4)

### 3.1. Studies Endpoint (`endpoints/studies.py`)
- [ ] `get_cancer_studies`
- [ ] `search_studies`
- [ ] `get_study_details`
- [ ] `get_multiple_studies`

### 3.2. Genes Endpoint (`endpoints/genes.py`)
- [ ] `search_genes`
- [ ] `get_genes`
- [ ] `get_multiple_genes`

### 3.3. Other Endpoints
- [ ] Samples (`samples.py`)
- [ ] Molecular Profiles (`molecular_profiles.py`)
- [ ] Gene Panels (`gene_panels.py`)

## 4. Phase 3: Server Core (Day 5)

### 4.1. Main Server Class (`server.py`)
- [ ] Refactor `CBioPortalMCPServer`
- [ ] Implement dependency injection
- [ ] Set up MCP tool registration
- [ ] Handle lifecycle events

### 4.2. Configuration
- [ ] Environment variable support
- [ ] Configuration validation
- [ ] Logging configuration

## 5. Phase 4: Testing (Completed)

### 5.1. Existing Test Coverage
- [x] Comprehensive test suite with 92 passing tests

### 5.1.1. Test Suite Alignment with APIClient (2025-05-20)
- [x] Refined `tests/test_server_lifecycle.py`:
  - [x] Updated logger mocks for `APIClient` and `CBioPortalMCPServer`.
  - [x] Adjusted log message assertions for startup/shutdown.
- [x] Refined `tests/test_snapshot_responses.py`:
  - [x] Corrected mock targets to `server_instance.api_client.make_api_request`.
  - [x] Overhauled mocking strategy for paginated list snapshot tests to align with `APIClient` and `paginate_results` utility behavior.
- [x] Test files include:
  - `test_server_lifecycle.py`
  - `test_pagination.py`
  - `test_multiple_entity_apis.py`
  - `test_input_validation.py`
  - `test_snapshot_responses.py`
  - `test_cli.py`
  - `test_error_handling.py`

### 5.2. Test Coverage
- [x] High test coverage achieved
- [x] Error conditions tested
- [x] Edge cases covered

### 5.3. Future Test Considerations
- [ ] Add performance benchmarks
- [ ] Monitor test coverage during refactoring

## 6. Phase 5: Documentation & Polish (Day 7)

### 6.1. Code Documentation
- [ ] Add/update docstrings
- [ ] Document public API
- [ ] Add type hints

### 6.2. Project Documentation
- [ ] Update README
- [ ] Add CONTRIBUTING guide
- [ ] Update CHANGELOG

### 6.3. Final Checks
- [ ] Linting
- [ ] Type checking
- [ ] Dependency updates

## 7. Rollout Strategy

1. **Current State**
   - [x] Comprehensive test suite in place
   - [x] Core functionality tested
   - [x] Error handling validated

2. **Incremental Refactoring**
   - [ ] Refactor one module at a time
   - [ ] Update tests as needed
   - [ ] Maintain backward compatibility
   - [ ] Ensure all tests pass after each change

3. **Documentation Updates**
   - [ ] Update CHANGELOG.md for each major change
   - [ ] Document new module structure
   - [ ] Update README with new architecture

4. **Final Steps**
   - [ ] Verify all tests pass
   - [ ] Update entry points if needed
   - [ ] Perform final code review
   - [ ] Update version number
   - [ ] Update documentation

## 8. Risk Mitigation

- **Risk**: Breaking changes
  - Mitigation: Maintain backward compatibility during transition
  - Test thoroughly before final switch

- **Risk**: Performance regression
  - Mitigation: Add performance benchmarks
  - Monitor during testing

- **Risk**: Incomplete test coverage
  - Mitigation: Set up code coverage requirements
  - Add missing tests before merging
