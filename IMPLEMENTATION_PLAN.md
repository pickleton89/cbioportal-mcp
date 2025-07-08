# cBioPortal MCP Server - Implementation Plan

## Executive Summary

Based on the comprehensive project analysis and current REFACTOR_PLAN.md, this document outlines the specific implementation steps for completing the modular refactoring of the cBioPortal MCP server.

**Project Status:** Excellent foundation with APIClient extraction complete and 92 passing tests
**Goal:** Transform monolithic server (1,352 lines) into maintainable modular architecture
**Timeline:** 5 days of focused development

## Current State Assessment

### ✅ Completed
- APIClient extraction with comprehensive testing (92 passing tests)
- Robust async implementation with 4.5x performance improvement
- Excellent test coverage and documentation
- Migration to uv package manager
- All tests passing with updated snapshots

### ❌ Remaining Work
- Monolithic server file (1,352 lines) needs modularization
- Utility functions scattered in main server
- Endpoint logic mixed in main server class
- Configuration file support missing
- No retry logic for transient failures

## Implementation Phases

### Phase 1: Utility Modules (Day 1)
**Priority: High** - Foundation for other modules

#### Tasks:
1. **Create `utils/` package structure:**
   ```
   utils/
   ├── __init__.py
   ├── pagination.py
   ├── validation.py
   └── logging.py
   ```

2. **Extract `utils/pagination.py`:**
   - Move `paginate_results()` function from main server
   - Extract pagination logic from endpoint methods
   - Add comprehensive pagination utilities
   - Update imports in main server

3. **Extract `utils/validation.py`:**
   - Move input validation helpers
   - Standardize validation patterns
   - Add parameter validation utilities

4. **Create `utils/logging.py`:**
   - Centralized logging configuration
   - Consistent log formatting
   - Environment-based log levels

#### Success Criteria:
- All tests pass (92 tests)
- Main server file reduced by ~200-300 lines
- Utility functions reusable across modules

### Phase 2: Endpoint Modules (Day 2-3)
**Priority: High** - Core business logic separation

#### Target Structure:
```
endpoints/
├── __init__.py
├── studies.py
├── genes.py
├── samples.py
└── molecular_profiles.py
```

#### Day 2: Studies and Genes Modules

1. **Create `endpoints/studies.py`:**
   - `get_cancer_studies()`
   - `search_studies()`
   - `get_study_details()`
   - `get_multiple_studies()`

2. **Create `endpoints/genes.py`:**
   - `search_genes()`
   - `get_genes()`
   - `get_multiple_genes()`
   - `get_mutations_in_gene()`

#### Day 3: Remaining Endpoints

3. **Create `endpoints/samples.py`:**
   - `get_samples_in_study()`
   - Sample-related utilities

4. **Create `endpoints/molecular_profiles.py`:**
   - `get_molecular_profiles()`
   - `get_clinical_data()`

#### Migration Strategy:
- Move endpoint methods with their specific logic
- Maintain same method signatures for compatibility
- Use dependency injection for APIClient
- Import and delegate from main server during transition

#### Success Criteria:
- All endpoint logic extracted from main server
- Main server file reduced to ~600-800 lines
- All 92 tests continue to pass
- Clear separation of concerns achieved

### Phase 3: Server Refactoring (Day 4)
**Priority: Medium** - Clean up main server class

#### Tasks:
1. **Refactor main `CBioPortalMCPServer` class:**
   - Remove extracted endpoint methods
   - Implement dependency injection pattern
   - Clean up tool registration logic
   - Streamline initialization

2. **Update `server.py` structure:**
   - MCP integration and coordination only
   - Tool registration and routing
   - Lifecycle management
   - Configuration handling

3. **Implement dependency injection:**
   - Inject APIClient into endpoint modules
   - Clean initialization pattern
   - Easier testing and mocking

#### Success Criteria:
- Main server class focused on MCP coordination
- Clear dependency injection pattern
- Simplified tool registration
- All tests pass with refactored structure

### Phase 4: Configuration Enhancement (Day 5)
**Priority: Medium** - Address configuration limitations

#### Tasks:
1. **Add configuration file support:**
   - YAML configuration file support
   - Environment variable integration
   - Configuration validation and defaults

2. **Create `config.py` module:**
   - Configuration class with validation
   - Environment variable handling
   - Default configuration values

3. **Enhance CLI interface:**
   - Support for config file path
   - Override config with CLI arguments
   - Better help and documentation

#### Success Criteria:
- Flexible configuration management
- Support for deployment configurations
- Backward compatibility maintained

## Testing Strategy

### Continuous Testing Approach:
- **After each module extraction:** Run full test suite (`uv run pytest`)
- **Update tests incrementally:** Modify imports and mocks as needed
- **Maintain 100% pass rate:** No broken tests during refactoring
- **Add module tests:** Create specific tests for new modules

### Test Updates Required:
- Update import statements in tests
- Modify mocks to target new module locations
- Add tests for utility functions
- Ensure endpoint module coverage

### Test Commands:
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=.

# Update snapshots if needed
uv run pytest --snapshot-update
```

## Risk Mitigation

### Technical Risks:
1. **Breaking Changes**
   - **Mitigation:** Maintain same public API during transition
   - **Strategy:** Import and delegate pattern during migration

2. **Test Failures**
   - **Mitigation:** Run tests after each change
   - **Strategy:** Fix immediately before proceeding

3. **Import Cycles**
   - **Mitigation:** Careful dependency design
   - **Strategy:** Clear module hierarchy and interfaces

### Process Risks:
1. **Scope Creep**
   - **Mitigation:** Stick to planned modules only
   - **Strategy:** Complete each phase before proceeding

2. **Performance Regression**
   - **Mitigation:** Maintain async patterns
   - **Strategy:** Profile critical paths if needed

## Success Metrics

### Quantitative Goals:
- **Main server file:** Reduce from 1,352 to ~400-500 lines
- **Test coverage:** Maintain 92 passing tests
- **Modularity:** 4-5 focused modules with clear responsibilities
- **Performance:** No regression in async performance

### Qualitative Goals:
- **Maintainability:** Easier to navigate and modify
- **Testability:** Cleaner unit testing of components
- **Extensibility:** Easy to add new endpoints
- **Documentation:** Clear module boundaries and responsibilities

## Next Steps

1. **Immediate:** Start with Phase 1 - Create utils package
2. **Priority:** Focus on `utils/pagination.py` first (highest impact)
3. **Validation:** Run `uv run pytest` after each module extraction
4. **Documentation:** Update CLAUDE.md after completion

## Notes

- This plan builds on the excellent foundation already established
- The comprehensive test suite provides confidence for refactoring
- The async architecture and APIClient extraction were excellent preparatory work
- Focus on maintainability while preserving all existing functionality

---

**Last Updated:** 2025-07-08
**Status:** Ready for implementation
**Next Phase:** Phase 1 - Utility Modules