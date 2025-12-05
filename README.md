# TinyDB MCP Server

A Model Context Protocol (MCP) server that provides tools and resources for interacting with TinyDB, a lightweight document-oriented database for Python.

## Overview

This MCP server enables AI assistants and other MCP clients to perform document database operations using TinyDB. It exposes both tools (for database operations) and resources (for reading database state).

## Features

### Tools
- **insert_document** - Insert a document into a table
- **query_documents** - Query documents with optional field/value filtering
- **update_documents** - Update documents matching specific criteria
- **delete_documents** - Delete documents (with optional filtering)
- **list_tables** - List all available tables in the database

### Resources
- **tinydb://stats** - Database statistics including document counts
- **tinydb://tables** - List of all tables with metadata
- **tinydb://table/{table_name}** - Contents of a specific table

## Installation

1. Clone the repository and navigate to the project directory

2. Install dependencies using uv:
```bash
uv sync
```

## Usage

### Running the Server

Start the MCP server using stdio transport:
```bash
python main.py
```

### Configuring MCP Client

Add this server to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "tinydb": {
      "command": "python",
      "args": ["/path/to/frosty-blackwell/main.py"]
    }
  }
}
```

Or using uv:
```json
{
  "mcpServers": {
    "tinydb": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/path/to/frosty-blackwell"
    }
  }
}
```

## Example Operations

### Insert a Document
```
Use the insert_document tool:
- data: {"name": "Alice", "age": 30, "city": "NYC"}
- table: "users"
```

### Query Documents
```
Use the query_documents tool:
- field: "city"
- value: "NYC"
- table: "users"

Or get all documents:
- table: "users"
(leave field and value empty)
```

### Update Documents
```
Use the update_documents tool:
- field: "name"
- value: "Alice"
- updates: {"age": 31}
- table: "users"
```

### Delete Documents
```
Use the delete_documents tool:
- field: "name"
- value: "Alice"
- table: "users"

WARNING: Calling without field/value will delete ALL documents!
```

### List Tables
```
Use the list_tables tool (no parameters needed)
```

### View Database Statistics
```
Read the tinydb://stats resource
```

### View Table Contents
```
Read the tinydb://table/users resource (replace 'users' with your table name)
```

## Database

The server creates a `tinydb_data.json` file in the project root to store all data. This file is created automatically on first use.

## Project Structure

```
frosty-blackwell/
├── src/
│   ├── __init__.py
│   └── mcp_tinydb_server.py   # Main server implementation
├── main.py                     # Entry point
├── pyproject.toml             # Dependencies
├── tinydb_data.json           # Database file (created on first use)
└── README.md                  # This file
```

## Development

### Requirements
- Python 3.14+
- mcp[cli] >= 1.23.1
- tinydb >= 4.8.0

### Testing

You can test the server using the MCP Inspector or any MCP client. The server runs over stdio transport and follows the MCP specification.

## License

See LICENSE file for details.