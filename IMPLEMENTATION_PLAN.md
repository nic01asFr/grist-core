# Implementation Plan: SQLite Extensions Integration

## Git Workflow Strategy

### Branch Structure
```
main (production)
  └── feature/sqlite-extensions (development branch)
       ├── Phase 1: sqlite-vec integration
       ├── Phase 2: SpatiaLite integration
       └── Phase 3: Hybrid queries
```

### Commit Strategy
- **Format**: Conventional Commits specification
- **Structure**: `type(scope): subject`
- **Types**: feat, fix, docs, test, refactor, perf, chore, build
- **Scope**: dockerfile, backend, sandbox, tests, docs
- **Subject**: Imperative mood, lowercase, no period, max 72 chars
- **Body** (optional): Detailed explanation, wrapped at 72 chars
- **Footer** (optional): Breaking changes, issue references

### Example Commits
```bash
# Good commit messages
feat(dockerfile): add sqlite-vec extension installation
test(backend): add sqlite-vec integration tests
refactor(sandbox): optimize vector search with sqlite-vec KNN
docs(readme): update CLAUDE.md with extension documentation

# Bad commit messages (avoid)
Updated files
Fixed bug
Added Claude Code improvements
WIP - testing stuff
```

## Quality Checklist Per Commit

Before each commit, verify:
- [ ] Code compiles without errors
- [ ] All existing tests pass
- [ ] New tests written for new functionality
- [ ] No debugging code (console.log, print statements)
- [ ] Code follows project style conventions
- [ ] Documentation updated if needed
- [ ] Commit message follows conventional format
- [ ] No secrets or sensitive data committed
- [ ] Docker builds successfully (if Dockerfile modified)

## Phase 1: sqlite-vec Integration (15-20 commits)

### Milestone 1.1: Extension Installation (3 commits)

**Commit 1**: `build(dockerfile): add sqlite-vec Python package`
```dockerfile
# In Dockerfile, Python dependencies section
RUN pip install sqlite-vec==0.1.0
```
- Files: `Dockerfile`
- Tests: Verify Docker build succeeds
- Validation: `docker build -t grist-test .`

**Commit 2**: `feat(backend): implement SQLite extension loading system`
```typescript
// In app/server/lib/SqliteNode.ts
private async _loadExtensions(): Promise<void> {
  const extensions = [
    { name: 'vec0', init: null, optional: true },
  ];
  // ... implementation
}
```
- Files: `app/server/lib/SqliteNode.ts`
- Tests: Unit tests for extension loading
- Validation: Extension loads without errors

**Commit 3**: `test(backend): add sqlite-vec extension integration tests`
- Files: `test/server/lib/testSqliteExtensions.ts` (new)
- Tests: Verify vec0 virtual table creation
- Validation: `npm test -- testSqliteExtensions`

### Milestone 1.2: Migration System (5 commits)

**Commit 4**: `feat(backend): add vec0 virtual table creation logic`
- Files: `app/server/lib/DocStorage.ts`
- Implementation: Virtual table creation for vector columns
- Tests: Table creation and verification

**Commit 5**: `feat(backend): implement vector column detection system`
- Files: `app/server/lib/VectorColumnDetector.ts` (new)
- Logic: Identify JSON array columns with numeric values
- Tests: Detection accuracy tests

**Commit 6**: `feat(backend): add incremental data migration for existing vectors`
- Files: `app/server/lib/VectorMigration.ts` (new)
- Implementation: Batch migration of JSON to vec0
- Tests: Migration integrity validation

**Commit 7**: `feat(backend): implement trigger system for vec0 synchronization`
- Files: `app/server/lib/DocStorage.ts`
- Triggers: INSERT, UPDATE, DELETE on vector columns
- Tests: Synchronization verification

**Commit 8**: `test(migration): add comprehensive migration test suite`
- Files: `test/server/lib/testVectorMigration.ts` (new)
- Coverage: Large datasets, edge cases, rollback
- Validation: All migration scenarios pass

### Milestone 1.3: Vector Search Optimization (4 commits)

**Commit 9**: `refactor(sandbox): add sqlite-vec backend option to VECTOR_SEARCH`
- Files: `sandbox/grist/embedding_manager.py`
- Implementation: Dual-mode search (Python fallback, sqlite-vec primary)
- Tests: Functional equivalence verification

**Commit 10**: `perf(sandbox): replace brute-force search with KNN when available`
- Files: `sandbox/grist/embedding_manager.py`
- SQL: `SELECT rowid, distance FROM vec0 WHERE vector MATCH ? ORDER BY distance LIMIT ?`
- Tests: Performance benchmarks (expect 10-50× improvement)

**Commit 11**: `feat(sandbox): add configurable distance metrics support`
- Files: `sandbox/grist/embedding_manager.py`
- Metrics: L2, cosine, inner product
- Tests: Metric accuracy validation

**Commit 12**: `test(sandbox): add vector search performance benchmarks`
- Files: `test/nbrowser/VectorSearchPerformance.ts` (new)
- Benchmarks: 1K, 10K, 100K records
- Validation: Document speedup ratios

### Milestone 1.4: VECTOR_SIMILARITY Optimization (3 commits)

**Commit 13**: `refactor(sandbox): optimize VECTOR_SIMILARITY with sqlite-vec`
- Files: `sandbox/grist/embedding_manager.py`
- Implementation: Direct vector comparison via extension
- Tests: Accuracy parity with Python scipy

**Commit 14**: `feat(sandbox): add batch similarity computation`
- Files: `sandbox/grist/embedding_manager.py`
- Use case: Compare one vector against multiple efficiently
- Tests: Batch vs. individual performance comparison

**Commit 15**: `test(sandbox): add similarity function edge case tests`
- Files: `test/nbrowser/VectorSimilarity.ts` (new)
- Edge cases: Zero vectors, identical vectors, orthogonal
- Validation: All edge cases handled correctly

### Milestone 1.5: Documentation & Cleanup (3 commits)

**Commit 16**: `docs(sandbox): add docstrings for optimized vector functions`
- Files: `sandbox/grist/embedding_manager.py`
- Documentation: Function signatures, parameters, examples
- Validation: Documentation completeness check

**Commit 17**: `refactor(backend): clean up error handling for extensions`
- Files: `app/server/lib/SqliteNode.ts`, `app/server/lib/DocStorage.ts`
- Improvements: Graceful degradation, informative warnings
- Tests: Error scenario coverage

**Commit 18**: `docs(project): update CLAUDE.md with sqlite-vec capabilities`
- Files: `CLAUDE.md`
- Sections: Installation, usage, performance characteristics
- Validation: Documentation review

## Phase 2: SpatiaLite Integration (25-30 commits)

### Milestone 2.1: Extension Installation (4 commits)

**Commit 19**: `build(dockerfile): add SpatiaLite system dependencies`
```dockerfile
RUN apt-get update && apt-get install -y \
    libspatialite7 \
    libspatialite-dev \
    spatialite-bin \
    && rm -rf /var/lib/apt/lists/*
```
- Files: `Dockerfile`
- Validation: Docker build, extension loading

**Commit 20**: `feat(backend): add mod_spatialite to extension loader`
- Files: `app/server/lib/SqliteNode.ts`
- Initialization: `SELECT InitSpatialMetadata(1)`
- Tests: Spatial metadata table creation

**Commit 21**: `test(backend): add SpatiaLite extension integration tests`
- Files: `test/server/lib/testSpatialiteExtension.ts` (new)
- Tests: Spatial metadata, basic ST_Distance query
- Validation: Extension fully operational

**Commit 22**: `feat(backend): implement spatial column detection system`
- Files: `app/server/lib/SpatialColumnDetector.ts` (new)
- Detection: WKT format validation (POINT, POLYGON, etc.)
- Tests: Format detection accuracy

### Milestone 2.2: Core Spatial Functions Module (8 commits)

**Commit 23**: `feat(sandbox): create spatial functions module structure`
- Files: `sandbox/grist/functions/spatial.py` (new)
- Structure: Base SQL executor, error handling
- Tests: Module import and basic execution

**Commit 24**: `feat(sandbox): implement geometry constructors (6 functions)`
- Functions: `ST_Point`, `ST_MakePoint`, `ST_MakeLine`, `ST_MakePolygon`, `ST_GeomFromText`, `ST_AsText`
- Files: `sandbox/grist/functions/spatial.py`
- Tests: WKT parsing and generation

**Commit 25**: `feat(sandbox): implement measurement functions (8 functions)`
- Functions: `ST_Distance`, `ST_Area`, `ST_Length`, `ST_Perimeter`, etc.
- Files: `sandbox/grist/functions/spatial.py`
- Tests: Precision validation against known values

**Commit 26**: `feat(sandbox): implement spatial relationships (10 functions)`
- Functions: `ST_Contains`, `ST_Intersects`, `ST_Within`, `ST_Overlaps`, etc.
- Files: `sandbox/grist/functions/spatial.py`
- Tests: Relationship logic correctness

**Commit 27**: `feat(sandbox): implement geometry processing (8 functions)`
- Functions: `ST_Buffer`, `ST_Centroid`, `ST_Intersection`, `ST_Union`, etc.
- Files: `sandbox/grist/functions/spatial.py`
- Tests: Geometry transformation accuracy

**Commit 28**: `feat(sandbox): implement coordinate transformations (5 functions)`
- Functions: `ST_Transform`, `ST_SetSRID`, `ST_SRID`, etc.
- Files: `sandbox/grist/functions/spatial.py`
- Tests: EPSG code handling

**Commit 29**: `feat(sandbox): implement validation functions (4 functions)`
- Functions: `ST_IsValid`, `ST_IsSimple`, `ST_IsEmpty`, etc.
- Files: `sandbox/grist/functions/spatial.py`
- Tests: Valid/invalid geometry detection

**Commit 30**: `feat(sandbox): implement geometry information functions (6 functions)`
- Functions: `ST_GeometryType`, `ST_NumGeometries`, `ST_Dimension`, etc.
- Files: `sandbox/grist/functions/spatial.py`
- Tests: Metadata extraction accuracy

### Milestone 2.3: Spatial Indexing (4 commits)

**Commit 31**: `feat(backend): add R-Tree spatial index creation`
- Files: `app/server/lib/DocStorage.ts`
- Implementation: Automatic R-Tree index for spatial columns
- Tests: Index creation and usage verification

**Commit 32**: `perf(backend): implement index-based spatial query optimization`
- Files: `app/server/lib/DocStorage.ts`
- Optimization: Use R-Tree for ST_Intersects, ST_Contains queries
- Tests: Performance benchmarks (expect 100-1000× improvement)

**Commit 33**: `feat(backend): add spatial index maintenance triggers`
- Files: `app/server/lib/DocStorage.ts`
- Triggers: Keep R-Tree synchronized with geometry changes
- Tests: Index consistency validation

**Commit 34**: `test(backend): add spatial index performance benchmarks`
- Files: `test/server/lib/testSpatialIndexPerformance.ts` (new)
- Benchmarks: Indexed vs. non-indexed queries on 10K+ geometries
- Validation: Document speedup metrics

### Milestone 2.4: Backward Compatibility (5 commits)

**Commit 35**: `refactor(sandbox): update existing ST_DISTANCE to use SpatiaLite`
- Files: `sandbox/grist/usertypes.py`
- Implementation: Delegate to SpatiaLite, fallback to Python
- Tests: Exact backward compatibility verification

**Commit 36**: `refactor(sandbox): update existing ST_AREA to use SpatiaLite`
- Files: `sandbox/grist/usertypes.py`
- Improvement: Handle polygon holes correctly
- Tests: Precision improvement validation

**Commit 37**: `refactor(sandbox): update existing ST_CONTAINS to use SpatiaLite`
- Files: `sandbox/grist/usertypes.py`
- Improvement: Support all geometry types
- Tests: Extended geometry support validation

**Commit 38**: `refactor(sandbox): update existing ST_CENTROID to use SpatiaLite`
- Files: `sandbox/grist/usertypes.py`
- Improvement: Weighted centroid for complex geometries
- Tests: Accuracy comparison

**Commit 39**: `test(sandbox): add backward compatibility regression tests`
- Files: `test/nbrowser/SpatialBackwardCompat.ts` (new)
- Coverage: All existing spatial formulas continue to work
- Validation: 100% formula compatibility

### Milestone 2.5: Frontend Integration (4 commits)

**Commit 40**: `feat(frontend): add spatial function autocomplete`
- Files: `app/client/components/FormulaEditor.ts`
- Implementation: Autocomplete for 50+ spatial functions
- Tests: Autocomplete suggestions accuracy

**Commit 41**: `feat(frontend): add spatial function documentation tooltips`
- Files: `app/client/components/FormulaEditor.ts`
- Content: Inline documentation for each spatial function
- Tests: Tooltip content validation

**Commit 42**: `feat(frontend): add geometry visualization widget`
- Files: `app/client/widgets/SpatialWidget.ts` (new)
- Implementation: Map-based geometry rendering (Leaflet)
- Tests: Rendering accuracy for all geometry types

**Commit 43**: `docs(frontend): add spatial functions user guide`
- Files: `documentation/spatial-functions.md` (new)
- Content: Usage examples, common patterns, tutorials
- Validation: Documentation completeness

## Phase 3: Hybrid Spatial-Vector Queries (8-10 commits)

### Milestone 3.1: Combined Query Infrastructure (3 commits)

**Commit 44**: `feat(sandbox): add SPATIAL_VECTOR_SEARCH hybrid function`
- Files: `sandbox/grist/functions/spatial.py`
- Signature: `SPATIAL_VECTOR_SEARCH(table, geometry_col, vector_col, bbox, query_vector, limit)`
- Implementation: Spatial filter + vector similarity ranking
- Tests: Functional correctness

**Commit 45**: `perf(sandbox): optimize hybrid queries with combined indexes`
- Files: `sandbox/grist/functions/spatial.py`
- Strategy: R-Tree spatial filter → vec0 KNN on subset
- Tests: Performance benchmarks

**Commit 46**: `feat(sandbox): add NEARBY_SIMILAR function`
- Signature: `NEARBY_SIMILAR(table, lat, lon, radius_km, description, limit)`
- Use case: "Find similar items within 5km of location"
- Tests: Real-world scenario validation

### Milestone 3.2: Advanced Use Cases (3 commits)

**Commit 47**: `feat(sandbox): add CLUSTER_SPATIAL function`
- Implementation: Spatial clustering with semantic similarity
- Algorithm: DBSCAN on coordinates, group by vector similarity
- Tests: Clustering quality metrics

**Commit 48**: `feat(sandbox): add ROUTE_OPTIMIZATION function`
- Use case: TSP with vector-based priority weighting
- Implementation: Spatial distance + semantic relevance scoring
- Tests: Route quality validation

**Commit 49**: `test(sandbox): add hybrid query performance benchmarks`
- Files: `test/nbrowser/HybridQueryPerformance.ts` (new)
- Benchmarks: Compare hybrid vs. separate queries
- Validation: Document performance characteristics

### Milestone 3.3: Final Documentation (2 commits)

**Commit 50**: `docs(project): comprehensive CLAUDE.md update`
- Files: `CLAUDE.md`
- Sections:
  - sqlite-vec installation and usage
  - SpatiaLite integration details
  - All 50+ spatial functions reference
  - Hybrid query patterns
  - Performance characteristics
  - Troubleshooting guide
- Validation: Complete documentation review

**Commit 51**: `docs(project): add migration guide for existing users`
- Files: `MIGRATION_GUIDE.md` (new)
- Content:
  - How to migrate existing spatial formulas
  - Performance optimization strategies
  - Breaking changes (if any)
  - Rollback procedures
- Validation: Migration guide completeness

## Validation & Testing Strategy

### Continuous Validation
After each commit:
1. **Build verification**: `docker-compose build`
2. **Unit tests**: `npm test`
3. **Python tests**: `pytest sandbox/grist/`
4. **Type checking**: `npm run typecheck`
5. **Linting**: `npm run lint`

### Integration Testing
After each milestone:
1. **Full build**: `docker-compose up --build`
2. **End-to-end tests**: `npm run test:nbrowser`
3. **Performance benchmarks**: Document before/after metrics
4. **Manual verification**: Test key user scenarios

### Pre-Merge Checklist
Before merging feature branch to main:
- [ ] All 50+ commits completed successfully
- [ ] Full test suite passes (unit + integration + e2e)
- [ ] Performance benchmarks documented
- [ ] All documentation updated (CLAUDE.md, MIGRATION_GUIDE.md)
- [ ] Docker image builds without warnings
- [ ] No regressions in existing functionality
- [ ] Code review completed (self-review + automated checks)
- [ ] Feature branch rebased on latest main

## Risk Mitigation

### Rollback Strategy
- Each phase is independently functional
- Can rollback to any milestone via Git
- Extension loading failures degrade gracefully to Python
- No data loss risk (migrations are additive, not destructive)

### Compatibility Preservation
- All existing formulas continue to work
- Python fallbacks for all SQLite extension features
- Incremental adoption (users can opt-in to new features)
- Semantic versioning for API changes

### Performance Regression Prevention
- Benchmark before/after for each optimization
- Never make existing queries slower
- Document performance characteristics clearly
- Provide opt-out mechanisms if needed

## Timeline Estimate

- **Phase 1** (sqlite-vec): 5-7 days, 18 commits
- **Phase 2** (SpatiaLite): 7-10 days, 30 commits
- **Phase 3** (Hybrid): 3-5 days, 8 commits
- **Total**: 15-22 days, 56 commits

## Success Criteria

1. ✅ All 56 commits merged to main without build failures
2. ✅ 100% backward compatibility with existing spatial formulas
3. ✅ 10-50× vector search performance improvement (benchmarked)
4. ✅ 50+ new spatial functions available and documented
5. ✅ Hybrid spatial-vector queries functional
6. ✅ Zero data loss during migrations
7. ✅ Comprehensive documentation complete
8. ✅ All tests passing (unit + integration + e2e)
