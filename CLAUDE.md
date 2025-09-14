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
- Python-based formula evaluation engine
- Sandboxed execution environment for user formulas
- SQLite-based document storage with in-memory data engine

**Static Assets (`static/`):**
- HTML templates, CSS, images, and localization files
- Custom widget templates and UI icons

### Key Architectural Patterns

**Document Model:**
- Each Grist document is a SQLite file (`.grist` format)
- Documents contain both data tables and metadata tables (prefixed with `_grist_`)
- Python data engine loads full document into memory for formula evaluation
- Exception: "on-demand" tables are loaded as needed

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
- Python sandbox for formula execution

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

## Development Workflow

1. Install dependencies with `yarn install` and `yarn install:python`
2. Run `yarn build` to compile TypeScript and generate bundles
3. Use `yarn start` for development with file watching
4. Run `yarn test` before committing changes
5. Use `yarn lint:fix` to address code style issues
6. Test specific functionality with targeted test commands

The codebase uses a sophisticated build system with TypeScript project references, enabling fast incremental builds and strong type checking across the entire application.