# cBioPortal MCP Server Refactoring Plan

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

## 5. Phase 4: Testing (Day 6)

### 5.1. Unit Tests
- [ ] Test API client
- [ ] Test endpoint handlers
- [ ] Test utilities

### 5.2. Integration Tests
- [ ] Test server initialization
- [ ] Test MCP registration
- [ ] Test end-to-end flows

### 5.3. Test Coverage
- [ ] Aim for 90%+ coverage
- [ ] Add missing test cases
- [ ] Test error conditions

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

1. **Initial Setup**
   - Create new package structure
   - Set up CI/CD pipeline
   - Configure testing environment

2. **Incremental Migration**
   - Move components one by one
   - Update tests as we go
   - Maintain backward compatibility

3. **Final Switch**
   - Update entry points
   - Update documentation
   - Deploy new version

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
