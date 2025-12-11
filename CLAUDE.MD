# CLAUDE.MD

This file contains information for Claude Code to better understand and work with this project.

## Project Overview

**Project Name:** mcp-tinydb-server

**Repository:** mcp-demo

**Current Branch:** frosty-blackwell (worktree)

**Main Branch:** main

**Description:** A Model Context Protocol (MCP) server that provides tools and resources for interacting with TinyDB, a lightweight document-oriented database for Python.

## Project Structure

```
mcp-tinydb-server/
├── .vscode/                    # VS Code configuration
│   ├── tasks.json             # Build and test tasks
│   ├── launch.json            # Debug configurations
│   ├── settings.json          # Project settings
│   └── extensions.json        # Recommended extensions
├── src/
│   ├── __init__.py
│   ├── mcp_tinydb_server.py   # Main server implementation
│   ├── config.py              # Pydantic Settings configuration
│   └── models.py              # Pydantic data models
├── tests/                      # Test suite (51 tests)
│   ├── __init__.py
│   ├── test_tinydb_manager.py
│   ├── test_tools.py
│   └── test_resources.py
├── main.py                     # Entry point
├── pyproject.toml             # Dependencies and project config
├── uv.lock                    # Dependency lock file
├── Dockerfile                 # Docker container configuration
├── docker-compose.yaml        # Docker Compose orchestration
├── .dockerignore              # Docker build exclusions
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
├── tinydb_data.json           # Database file (created on first use)
├── README.md                  # User documentation
├── CLAUDE.MD                  # This file
├── LICENSE
└── .gitignore
```

## Development Context

### Git Workflow
- This is a git worktree located at: `/Users/wconklin/.claude-worktrees/mcp-demo/frosty-blackwell`
- Main repository location: `/Users/wconklin/Code/GitHub/mcp-demo`
- Current working branch: `frosty-blackwell`
- Main branch for PRs: `main`

### Current Status
- ✅ Full MCP server implementation complete
- ✅ Comprehensive test suite (44/44 tests passing)
- ✅ Complete documentation
- ✅ PR #1 created and review feedback addressed
- Last commit: c790975 - "fix: address PR review feedback"

### Recent Commits
```
c790975 fix: address PR review feedback
10cae5a docs: fix MCP client configuration and add troubleshooting
9bcb07f test: add comprehensive test suite
ec8bbb5 docs: add project documentation
83fd24d feat: implement TinyDB MCP server
7220742 build: initialize project with dependencies
4205d5b Initial commit
```

## Configuration

The server uses Pydantic Settings for configuration management. Settings can be configured via:
1. Environment variables
2. `.env` file (copy from `.env.example`)
3. Default values

**Available Settings:**
- `TINYDB_PATH`: Path to database file (default: `tinydb_data.json`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `ENABLE_LOGFIRE`: Enable Logfire remote logging (default: `false`)
- `LOGFIRE_TOKEN`: API token for Logfire (optional)
- `SERVER_NAME`: Server name (default: `TinyDB MCP Server`)
- `SERVER_VERSION`: Server version (default: `0.1.0`)

**Example .env file:**
```bash
TINYDB_PATH=data/my_database.json
LOG_LEVEL=DEBUG
ENABLE_LOGFIRE=false
```

## Commands & Scripts

### Install Dependencies
```bash
uv sync
```

### Run MCP Server

**Local (Development):**
```bash
python main.py
```

**Docker (Production):**
```bash
# Using docker-compose
docker-compose up -d

# Or using Docker directly
docker build -t mcp-tinydb-server .
docker run -it --rm -v tinydb-data:/data mcp-tinydb-server
```

### Run Tests
```bash
uv run pytest tests/ -v
```

### Test Specific Module
```bash
uv run pytest tests/test_tools.py -v
uv run pytest tests/test_resources.py -v
uv run pytest tests/test_tinydb_manager.py -v
```

### Lint Code
```bash
# Check for linting issues
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Type Check
```bash
# Run ty type checker
uv run ty check
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks (one-time setup)
uv run pre-commit install

# Run hooks manually on all files
uv run pre-commit run --all-files

# Run hooks on staged files only
uv run pre-commit run

# Update hook versions
uv run pre-commit autoupdate
```

**Hooks configured:**
- Ruff linting (with auto-fix)
- Ruff formatting
- TruffleHog secrets scanner (blocks commits containing secrets)
- ty type checking (Astral's fast type checker)
- Pytest (runs full test suite)

**Note:** Hooks run automatically on every commit to ensure code quality and security.

### VS Code Tasks

**Quick Commands:**
- Press `⇧⌘B` (Cmd+Shift+B) to run default build task (Docker: Build Image)
- Press `⇧⌘T` to open test panel
- Press `F5` to start debugger

**Available Tasks** (Run via `Cmd+Shift+P` → "Tasks: Run Task"):

**Testing:**
- Run All Tests (default test task)
- Run Tests with Coverage
- Run Specific Test File

**Code Quality:**
- Lint with Ruff
- Fix with Ruff
- Format with Ruff
- Type Check (ty)
- Run Pre-commit Hooks
- Full Quality Check (lint + format + ty + test)

**Docker:**
- Docker: Build Image (default build task)
- Docker: Start with Compose
- Docker: Stop Compose
- Docker: View Logs
- Docker: Rebuild and Restart
- Docker: Run Interactive

**Development:**
- Run MCP Server (Local)
- Install Dependencies
- Install Pre-commit Hooks
- Build and Test

**Debug Configurations:**
- Run MCP Server (F5)
- Run Current Test File
- Run All Tests
- Run Tests with Coverage
- Docker: Attach to Running Container

**Recommended Extensions:**
- Python, Pylance, Ruff
- Docker, YAML, TOML
- GitLens, Markdown

See `.vscode/` directory for complete configuration.

### MCP Server Configuration

**Claude Desktop Config Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Recommended: Docker Configuration**
```json
{
  "mcpServers": {
    "tinydb": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--name", "mcp-tinydb-claude",
        "-v", "mcp-tinydb-data:/data",
        "mcp-tinydb-server"
      ]
    }
  }
}
```

**Alternative: Local Development**
- Use absolute path to `uv` command (find with `which uv`)
- Point to project directory

### Logs Location
- macOS: `~/Library/Logs/Claude/mcp-server-tinydb.log`

## Architecture & Patterns

### Framework
- **FastMCP**: Decorator-based MCP server framework
- **Transport**: stdio (standard for MCP servers)
- **Database**: TinyDB with JSON file storage
- **Configuration**: Pydantic Settings with environment variables
- **Logging**: Logfire for structured logging and observability
- **Models**: Pydantic models for data validation

### Design Decisions
1. **Synchronous Operations**: TinyDB is sync-only, no async wrappers needed
2. **Lazy Database Initialization**: Database created on first access via property
3. **Table-based Organization**: Uses TinyDB's native table feature
4. **Required Parameters for Deletion**: Security feature to prevent accidental data loss
5. **Comprehensive Error Handling**: All operations wrapped in try-except with user-friendly errors
6. **Automated Security Scanning**: TruffleHog pre-commit hook prevents committing secrets
7. **Containerization**: Docker support for isolated, portable deployment
8. **Configurable Database Path**: Environment variable support for flexible deployment

### MCP Server Components

**Tools (5)**:
1. `insert_document` - Insert a document into a table
2. `query_documents` - Query documents with optional field/value filtering
3. `update_documents` - Update documents matching specific criteria
4. `delete_documents` - Delete documents (requires field and value for safety)
5. `list_tables` - List all available tables in the database

**Resources (3)**:
1. `tinydb://stats` - Database statistics including document counts
2. `tinydb://tables` - List of all tables with metadata
3. `tinydb://table/{table_name}` - Contents of a specific table

### Code Organization
- **TinyDBManager Class** (src/mcp_tinydb_server.py:11-84): Handles all database operations
- **MCP Tools** (src/mcp_tinydb_server.py:100-266): Decorated functions exposed to MCP clients
- **MCP Resources** (src/mcp_tinydb_server.py:270-374): URI-based database state access
- **Entry Point** (main.py): Simple import and run

## Dependencies

### Production
- **mcp[cli] >= 1.23.1**: Model Context Protocol framework with CLI tools (includes Pydantic)
- **tinydb >= 4.8.0**: Lightweight document-oriented database
- **pydantic-settings >= 2.0.0**: Configuration management with environment variables
- **logfire >= 0.1.0**: Structured logging and observability from Pydantic team

### Development
- **pytest >= 8.0.0**: Testing framework
- **ruff >= 0.8.0**: Fast Python linter and code formatter
- **ty >= 0.0.1a32**: Fast static type checker from Astral (alpha)
- **pre-commit >= 4.0.0**: Git hook framework for automated quality checks
- **trufflehog** (system): Secrets detection and prevention (installed via Homebrew)

### Python Version
- Requires Python >= 3.14
- Ruff target version: Python 3.13 (for pre-commit compatibility)

## Testing

### Test Coverage
**Original Tests (51)**:
- **9 tests**: TinyDBManager class functionality
- **23 tests**: All MCP tools (insert, query, update, delete, list)
- **14 tests**: All MCP resources (stats, tables, table contents)
- **7 tests**: Integration tests (full CRUD workflow, multi-table, resources, error handling, persistence, bulk ops)

**New Comprehensive Tests (111)**:
- **36 tests**: Pydantic model validation (test_models.py)
- **20 tests**: Error handling and edge cases (test_error_handling.py)
- **22 tests**: Unicode and special characters (test_unicode.py)
- **14 tests**: Configuration and settings (test_config.py)
- **19 tests**: Resource error handling (test_resource_errors.py)

**Total**: 162 tests, all passing | **Coverage**: 93.47%

### Test Files
- `tests/test_tinydb_manager.py` - Database manager unit tests
- `tests/test_tools.py` - MCP tool tests
- `tests/test_resources.py` - MCP resource tests
- `tests/test_integration.py` - End-to-end integration tests
- `tests/test_models.py` - Pydantic model validation tests
- `tests/test_error_handling.py` - Error scenarios and edge cases
- `tests/test_unicode.py` - Unicode and special character tests
- `tests/test_config.py` - Configuration and settings tests
- `tests/test_resource_errors.py` - Resource-specific error tests
- `tests/conftest.py` - Shared fixtures and pytest configuration

### Test Strategy
- Each test uses isolated temporary database
- Automatic cleanup after each test
- Tests cover success cases, error cases, and edge cases
- No test relies on external state or real database file
- Pytest markers for slow, corruption, and permission tests
- Comprehensive fixtures for corrupted files, large data, unicode

## Coding Standards

### Commit Messages
- Use Conventional Commits syntax: `type: description`
- Types: `feat`, `fix`, `docs`, `test`, `build`, `refactor`


### Code Style
- Type hints for all function parameters and returns
- Comprehensive docstrings with Args and Returns sections
- Error handling with try-except and informative error messages
- Validation of input parameters before operations
- PEP 8 compliant (enforced by ruff and pre-commit)
- 100 character line length
- Double quotes for strings
- Sorted imports (isort style)
- Automated quality checks via pre-commit hooks

### Test Coverage Requirements
- **Commits**: Minimum 40% test coverage required for all commits
- **Pull Requests**: Minimum 70% test coverage required for PR approval
- **Current Coverage**: 93.47% (162 tests passing)
- **Coverage Tools**: pytest-cov with HTML and terminal reporting
- **Run Coverage**: `uv run pytest tests/ --cov=src --cov-report=term --cov-report=html`
- **View Report**: Open `htmlcov/index.html` in browser after generating coverage

## Known Issues & Limitations

None currently. All PR review feedback has been addressed.

## Docker Deployment

### Container Features
- **Base Image**: Python 3.14-slim for minimal size
- **Package Manager**: UV for fast dependency installation
- **User**: Non-root user (mcpuser, UID 1000) for security
- **Data Persistence**: Docker volume mounted at `/data`
- **Environment**: Configurable via `TINYDB_PATH` env var

### Quick Start
```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Volume Management
The database is persisted in a Docker named volume:
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect frosty-blackwell_tinydb-data

# Backup database
docker run --rm -v frosty-blackwell_tinydb-data:/data -v $(pwd):/backup alpine tar czf /backup/tinydb-backup.tar.gz -C /data .

# Restore database
docker run --rm -v frosty-blackwell_tinydb-data:/data -v $(pwd):/backup alpine tar xzf /backup/tinydb-backup.tar.gz -C /data
```

## Future Enhancements (Potential)

- Advanced query support (beyond simple equality)
- Batch operations for better performance
- Database backup/restore functionality (partially addressed via Docker volumes)
- Query result pagination for large datasets
- Support for custom serializers
- Kubernetes deployment manifests

---

Last updated: 2025-12-07
