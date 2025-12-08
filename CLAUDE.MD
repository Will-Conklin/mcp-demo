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
├── src/
│   ├── __init__.py
│   └── mcp_tinydb_server.py   # Main server implementation
├── tests/                      # Test suite (44 tests)
│   ├── __init__.py
│   ├── test_tinydb_manager.py
│   ├── test_tools.py
│   └── test_resources.py
├── main.py                     # Entry point
├── pyproject.toml             # Dependencies and project config
├── uv.lock                    # Dependency lock file
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

## Commands & Scripts

### Install Dependencies
```bash
uv sync
```

### Run MCP Server
```bash
python main.py
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
- Pytest (runs full test suite)

**Note:** Hooks run automatically on every commit to ensure code quality.

### MCP Server Configuration
The server is configured in Claude Desktop at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Use absolute path to `uv` command (find with `which uv`)

### Logs Location
- macOS: `~/Library/Logs/Claude/mcp-server-tinydb.log`

## Architecture & Patterns

### Framework
- **FastMCP**: Decorator-based MCP server framework
- **Transport**: stdio (standard for MCP servers)
- **Database**: TinyDB with JSON file storage

### Design Decisions
1. **Synchronous Operations**: TinyDB is sync-only, no async wrappers needed
2. **Lazy Database Initialization**: Database created on first access via property
3. **Table-based Organization**: Uses TinyDB's native table feature
4. **Required Parameters for Deletion**: Security feature to prevent accidental data loss
5. **Comprehensive Error Handling**: All operations wrapped in try-except with user-friendly errors

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
- **mcp[cli] >= 1.23.1**: Model Context Protocol framework with CLI tools
- **tinydb >= 4.8.0**: Lightweight document-oriented database

### Development
- **pytest >= 8.0.0**: Testing framework
- **ruff >= 0.8.0**: Fast Python linter and code formatter
- **pre-commit >= 4.0.0**: Git hook framework for automated quality checks

### Python Version
- Requires Python >= 3.14
- Ruff target version: Python 3.13 (for pre-commit compatibility)

## Testing

### Test Coverage
- **9 tests**: TinyDBManager class functionality
- **23 tests**: All MCP tools (insert, query, update, delete, list)
- **14 tests**: All MCP resources (stats, tables, table contents)
- **Total**: 44 tests, all passing

### Test Strategy
- Each test uses isolated temporary database
- Automatic cleanup after each test
- Tests cover success cases, error cases, and edge cases
- No test relies on external state or real database file

## Coding Standards

### Commit Messages
- Use Conventional Commits syntax: `type: description`
- Types: `feat`, `fix`, `docs`, `test`, `build`, `refactor`
- Include Claude Code attribution footer:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

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

## Known Issues & Limitations

None currently. All PR review feedback has been addressed.

## Future Enhancements (Potential)

- Advanced query support (beyond simple equality)
- Batch operations for better performance
- Database backup/restore functionality
- Query result pagination for large datasets
- Support for custom serializers

---

Last updated: 2025-12-07
