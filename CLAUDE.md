# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Build and Development
```bash
# Install dependencies
yarn install
yarn install:python

# Build the application
yarn build          # Development build
yarn build:prod     # Production build

# Start development server
yarn start          # Development mode with watch
yarn start:prod     # Production mode

# Debugging
yarn start:debug        # Start with Node.js inspector
yarn start:debug-brk    # Start with Node.js inspector and break
```

### Testing
```bash
# Run all tests
yarn test

# Run specific test suites
yarn test:client        # Client-side tests
yarn test:server        # Server-side tests  
yarn test:common        # Common utility tests
yarn test:gen-server    # Generic server tests
yarn test:nbrowser      # Browser integration tests
yarn test:python        # Python sandbox tests

# Run tests with debugging
yarn test:debug
yarn test:nbrowser:debug

# Run specific tests using grep pattern
GREP_TESTS=ActionLog yarn test
GREP_TESTS=summary yarn test:python
```

### Code Quality
```bash
# Lint code
yarn lint           # Check for linting errors
yarn lint:fix       # Fix auto-fixable linting errors  
yarn lint:ci        # Lint with zero warnings (CI mode)

# Generate translation keys and schemas
yarn generate:translation
yarn generate:schema:ts
yarn generate:icons
```

### Single Test Execution
```bash
# Run a single test file
yarn test '_build/test/server/specific-test.js'

# Run browser tests for a specific component
GREP_TESTS=WidgetName yarn test:nbrowser

# Run tests with stubs (mocked external services)
yarn test:stubs

# Smoke test for quick validation
yarn test:smoke
```

## Architecture Overview

Grist is a hybrid database-spreadsheet application with a multi-tier architecture:

### Core Components

**App Structure (`app/`):**
- `app/client/` - Frontend TypeScript/JavaScript code using GrainJS framework
- `app/server/` - Backend Node.js server code  
- `app/common/` - Shared code between client and server
- `app/gen-server/` - Generic server components for multi-instance deployments
- `app/plugin/` - Plugin system and API definitions

**Data Engine (`sandbox/`):**
- Python-based formula evaluation engine with embedding and spatial functions
- Sandboxed execution environment for user formulas
- SQLite-based document storage with in-memory data engine
- Auto-embedding manager for vectorial data processing
- Spatial geometry processing capabilities

**Static Assets (`static/`):**
- HTML templates, CSS, images, and localization files
- Custom widget templates and UI icons

### Key Architectural Patterns

**Document Model:**
- Each Grist document is a SQLite file (`.grist` format)
- Documents contain both data tables and metadata tables (prefixed with `_grist_`)
- Python data engine loads full document into memory for formula evaluation
- Exception: "on-demand" tables are loaded as needed
- Support for Vector and Geometry data types for advanced analytics

**Server Architecture:**
- **Home Servers**: Handle user management, document access, API requests
- **Doc Workers**: Handle document operations, maintain document state, run Python sandbox
- Load balancing via ALB for scalable deployments
- WebSocket communication for real-time updates

**Client-Server Communication:**
- REST API for document management and data operations
- WebSocket for real-time collaborative editing  
- Browser maintains local document state synchronized with server

### Technology Stack

**Frontend:**
- TypeScript/JavaScript with GrainJS reactive framework
- Webpack for bundling, ESLint for linting
- Backbone.js models, jQuery for DOM manipulation
- Custom widget system for extensibility

**Backend:**
- Node.js with Express server framework
- TypeORM for database operations (PostgreSQL/SQLite)
- Redis for session management and worker coordination
- Python sandbox for formula execution with embedding and spatial capabilities
- Integration with external AI services (Albert API) for embedding generation

**Build System:**
- Yarn package manager
- Custom build scripts in `buildtools/`
- TypeScript compilation with project references
- Webpack configuration for client bundles

### Development Patterns

**Project Structure:**
- Monorepo with TypeScript project references (`tsconfig.json` references)
- Shared interfaces generated with `ts-interface-builder` 
- Consistent import patterns: `app/client/`, `app/server/`, `app/common/`

**Testing Strategy:**
- Unit tests for individual components (`test/common/`, `test/client/`, `test/server/`)
- Integration tests for full workflows (`test/nbrowser/`)
- Python tests for data engine functionality (`test/python/`)
- Browser automation via `mocha-webdriver`

**Code Conventions:**
- ESLint with TypeScript rules enforced
- Member ordering conventions for class definitions
- Private members prefixed with underscore
- 120-character line length limit

## Environment Configuration

Key environment variables for development:
- `GRIST_TEST_LOGIN=1` - Enable test authentication
- `GRIST_DEFAULT_EMAIL` - Set default user email for development
- `GRIST_SANDBOX_FLAVOR` - Sandbox type (gvisor, docker, unsandboxed, pyodide)
- `DEBUG=1` - Enable debug mode for tests
- `GREP_TESTS` - Filter tests by pattern

### Embedding and AI Integration
- `ALBERT_API_TOKEN` - API token for Albert embedding service
- `ALBERT_API_URL` - Base URL for Albert API (default: https://albert.api.etalab.gouv.fr/v1)
- `ALBERT_MODEL_EMBEDDING` - Model name for embeddings (default: embeddings-small)

### Advanced Features
- `NO_CLEANUP=1` - Disable test cleanup for debugging
- `MOCHA_WEBDRIVER_HEADLESS=1` - Run browser tests in headless mode
- `MOCHA_WEBDRIVER_LOGDIR` - Directory for webdriver logs during testing

## Development Workflow

1. Install dependencies with `yarn install` and `yarn install:python`
2. Run `yarn build` to compile TypeScript and generate bundles
3. Use `yarn start` for development with file watching
4. Run `yarn test` before committing changes
5. Use `yarn lint:fix` to address code style issues
6. Test specific functionality with targeted test commands

## Advanced Features

### Extended Data Types

This fork includes two custom data types for advanced analytics:

**Geometry Type** (`sandbox/grist/usertypes.py`):
- WKT (Well-Known Text) format for spatial data
- Supports: POINT, LINESTRING, POLYGON, MULTIPOINT, etc.
- GeoJSON conversion for basic geometries
- Default value: None

**Vector Type** (`sandbox/grist/usertypes.py`):
- Arrays of floating-point numbers for ML embeddings
- JSON/CSV string parsing support
- Optional dimension validation
- Common use: OpenAI (1536d), Albert (1024d) embeddings

### Geospatial Functions

All functions are implemented in Python (`sandbox/grist/usertypes.py`) and registered in `sandbox/grist/main.py`:

**Spatial Operations:**
- `ST_DISTANCE(point1, point2, unit)` - Haversine distance between points (m/km/deg)
- `ST_AREA(polygon, unit)` - Polygon area calculation (m²/km²/ha)
- `ST_CONTAINS(polygon, point)` - Point-in-polygon test via ray casting
- `ST_CENTROID(polygon)` - Geometric center (returns WKT Point)

**Vector Operations:**
- `VECTOR_SIMILARITY(vec1, vec2, method)` - Similarity metrics (cosine/euclidean/dot)

Usage in formulas:
```python
# Distance between Paris locations
grist.ST_DISTANCE($Location_A, $Location_B, 'km')

# Area of a zone
grist.ST_AREA($Zone_Polygon, 'ha')

# Find if point is in region
grist.ST_CONTAINS($Region, $User_Location)
```

### Auto-Embedding System

**Architecture** (`sandbox/grist/embedding_manager.py`):

1. **AutoEmbeddingManager** - Core service managing:
   - External API integration (Albert API, OpenAI)
   - Text aggregation from multiple columns
   - Content hash-based change detection (MD5)
   - Embedding generation queue

2. **System Fields** (automatically created):
   - `_grist_record_embedding` (Text/JSON) - Stores embedding vector
   - `_grist_embedding_hash` (Text) - MD5 hash for change detection
   - `_grist_embedding_status` (Choice) - Generation status
   - `_grist_embedding_updated` (DateTime) - Last update timestamp

3. **Python Functions** (registered in `main.py:264-276`):
   - `AUTO_EMBEDDING(table_id, row_id, service='albert')` - Generate embedding
   - `VECTOR_SEARCH_SYSTEM(table_id, query, limit=10, threshold=0.7)` - Semantic search
   - `CREATE_SYSTEM_EMBEDDING_FIELDS(table_id)` - Initialize table fields

**Auto-Detection Logic**:
- Scans all text columns (excludes `_grist_*`, formulas, IDs)
- Computes content hash to avoid redundant API calls
- Returns `{embedding: float[], hash: string, dimensions: int}`

**API Configuration**:
```bash
ALBERT_API_TOKEN=your_token_here
ALBERT_API_URL=https://albert.api.etalab.gouv.fr/v1
ALBERT_MODEL_EMBEDDING=embeddings-small  # 1024 dimensions
```

### REST API Endpoints

**Spatial/Vector Endpoints** (`app/server/lib/SpatialEndpoints.ts`):
```
POST /api/docs/:docId/spatial/distance       # Calculate distance
POST /api/docs/:docId/spatial/area           # Calculate polygon area
POST /api/docs/:docId/spatial/contains       # Test containment
POST /api/docs/:docId/vector/similarity      # Vector similarity
POST /api/docs/:docId/spatial/batch/distances         # Batch distance calculations
POST /api/docs/:docId/vector/batch/similarities       # Batch similarity calculations
GET  /api/docs/:docId/spatial/capabilities   # List available functions
GET  /api/docs/:docId/spatial/health         # Health check
```

**Embedding Endpoints** (`app/server/lib/EmbeddingEndpoints.ts`):
```
POST /api/docs/:docId/tables/:tableId/embedding/configure   # Setup auto-embedding
GET  /api/docs/:docId/tables/:tableId/embedding/config      # Get configuration
POST /api/docs/:docId/tables/:tableId/search/semantic       # Semantic search
POST /api/docs/:docId/tables/:tableId/embedding/generate    # Generate embeddings
GET  /api/docs/:docId/embedding/status                       # Global status
```

### Python-TypeScript Integration Pattern

All endpoints use this pattern to call Python sandbox functions:

```typescript
// 1. Get ActiveDoc from DocManager
const session = docSessionFromRequest(req);
const activeDoc = await docManager.fetchDoc(session, docId);

// 2. Access Python sandbox via _dataEngine
const dataEngine = await activeDoc._dataEngine;
const result = await dataEngine.pyCall(functionName, arg1, arg2, ...);

// 3. Persist results via UserActions (if needed)
await activeDoc.applyUserActions(docSession, [[
  'BulkUpdateRecord',
  tableId,
  rowIds,
  { _grist_record_embedding: embeddingValues }
]]);
```

**Fallback Strategy**: Endpoints include TypeScript mocks for development/testing when Python sandbox is unavailable.

### Docker and Container Support

- **Dockerfile.spatial** - Includes geospatial libraries (GDAL, Shapely)
- **Dockerfile.extensions** - Full build with embedding + spatial support
- Multiple environment-specific configurations for deployment
- Configurable sandbox flavors (gvisor, docker, unsandboxed, pyodide)

### Development Notes

**Code Conventions**:
- ESLint enforces TypeScript rules (`.eslintrc.js`)
- Private members prefixed with `_` and use camelCase
- Member ordering: static fields → fields → constructor → methods
- Max line length: 120 characters
- Import sorting enforced (case-insensitive)

**Testing Strategy**:
- Unit tests for Python functions: `yarn test:python`
- Integration tests for endpoints: `yarn test:server`
- Browser tests for UI: `yarn test:nbrowser`
- Test-specific scripts in root: `test_embedding_*.py`, `test_*_workflow*.py`

**TypeScript Project Structure**:
- Uses project references (`tsconfig.json`) for incremental builds
- Shared interfaces generated with `ts-interface-builder`
- Webpack bundles for client-side code

The codebase uses a sophisticated build system with TypeScript project references, enabling fast incremental builds and strong type checking across the entire application.