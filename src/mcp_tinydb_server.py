"""MCP Server for TinyDB document database operations."""

import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from tinydb import Query, TinyDB


class TinyDBManager:
    """Manager class for TinyDB database operations."""

    def __init__(self, db_path: str = "tinydb_data.json"):
        """Initialize the TinyDB manager.

        Args:
            db_path: Path to the TinyDB database file
        """
        self.db_path = db_path
        self._db = None

    @property
    def db(self) -> TinyDB:
        """Lazy initialization of database.

        Returns:
            TinyDB instance
        """
        if self._db is None:
            self._db = TinyDB(self.db_path)
        return self._db

    def get_table(self, table_name: str):
        """Get or create a table.

        Args:
            table_name: Name of the table

        Returns:
            TinyDB Table instance
        """
        return self.db.table(table_name)

    def get_all_tables(self) -> list[str]:
        """Get list of all table names.

        Returns:
            List of table names
        """
        return list(self.db.tables())

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary containing database statistics
        """
        stats = {
            "database_path": os.path.abspath(self.db_path),
            "total_tables": len(self.db.tables()),
            "tables": {}
        }

        # Get file size if database file exists
        if os.path.exists(self.db_path):
            stats["database_size_bytes"] = os.path.getsize(self.db_path)
        else:
            stats["database_size_bytes"] = 0

        # Get document count per table
        for table_name in self.db.tables():
            table = self.get_table(table_name)
            stats["tables"][table_name] = {
                "document_count": len(table)
            }

        return stats

    def close(self):
        """Close database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None


# Initialize FastMCP server
mcp = FastMCP(
    name="TinyDB MCP Server",
    instructions="A Model Context Protocol server for TinyDB operations. "
                 "Provides tools for document insertion, querying, updating, "
                 "and deletion, plus resources for database statistics."
)

# Initialize database manager
db_manager = TinyDBManager()


# Tools
@mcp.tool()
def insert_document(data: dict, table: str = "default") -> dict:
    """Insert a document into TinyDB.

    Args:
        data: Dictionary containing the document data to insert
        table: Table name (default: "default")

    Returns:
        Dictionary with the inserted document ID
    """
    try:
        # Validate data is a dictionary
        if not isinstance(data, dict):
            return {
                "success": False,
                "error": f"Data must be a dictionary, got {type(data).__name__}"
            }

        # Get table and insert document
        tbl = db_manager.get_table(table)
        doc_id = tbl.insert(data)

        return {
            "success": True,
            "document_id": doc_id,
            "table": table
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def query_documents(field: str | None = None, value: Any | None = None,
                   table: str = "default") -> dict:
    """Query documents from TinyDB.

    Args:
        field: Field name to query (optional, returns all if None)
        value: Value to match (required if field is provided)
        table: Table name (default: "default")

    Returns:
        Dictionary with list of matching documents
    """
    try:
        tbl = db_manager.get_table(table)

        # If no field/value, return all documents
        if field is None:
            documents = tbl.all()
        else:
            # Validate that value is provided if field is specified
            if value is None:
                return {
                    "success": False,
                    "error": "Value must be provided when field is specified"
                }

            # Search using equality query
            q = Query()
            documents = tbl.search(q[field] == value)

        return {
            "success": True,
            "table": table,
            "count": len(documents),
            "documents": documents
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def update_documents(field: str, value: Any, updates: dict,
                    table: str = "default") -> dict:
    """Update documents matching criteria.

    Args:
        field: Field name to match
        value: Value to match
        updates: Dictionary of fields to update
        table: Table name (default: "default")

    Returns:
        Dictionary with count of updated documents
    """
    try:
        # Validate updates is a dictionary
        if not isinstance(updates, dict):
            return {
                "success": False,
                "error": f"Updates must be a dictionary, got {type(updates).__name__}"
            }

        tbl = db_manager.get_table(table)
        q = Query()

        # Update documents matching the criteria
        doc_ids = tbl.update(updates, q[field] == value)

        return {
            "success": True,
            "table": table,
            "updated_count": len(doc_ids) if isinstance(doc_ids, list) else (1 if doc_ids else 0)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def delete_documents(field: str, value: Any, table: str = "default") -> dict:
    """Delete documents from TinyDB matching specific criteria.

    Args:
        field: Field name to match (required)
        value: Value to match (required)
        table: Table name (default: "default")

    Returns:
        Dictionary with count of deleted documents
    """
    try:
        tbl = db_manager.get_table(table)
        q = Query()
        doc_ids = tbl.remove(q[field] == value)

        return {
            "success": True,
            "table": table,
            "deleted_count": len(doc_ids) if isinstance(doc_ids, list) else (1 if doc_ids else 0)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def list_tables() -> dict:
    """List all available tables/collections in the database.

    Returns:
        Dictionary with list of table names
    """
    try:
        tables = db_manager.get_all_tables()
        return {
            "success": True,
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Resources
@mcp.resource("tinydb://stats")
def get_database_stats() -> str:
    """Get database statistics including document counts per table.

    Returns:
        JSON string with database statistics
    """
    try:
        stats = db_manager.get_stats()

        # Format as a readable text response
        lines = [
            "=== TinyDB Database Statistics ===",
            f"Database Path: {stats['database_path']}",
            f"Database Size: {stats['database_size_bytes']} bytes",
            f"Total Tables: {stats['total_tables']}",
            ""
        ]

        if stats['tables']:
            lines.append("Tables:")
            for table_name, table_info in stats['tables'].items():
                lines.append(f"  - {table_name}: {table_info['document_count']} documents")
        else:
            lines.append("No tables found in database")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting database statistics: {str(e)}"


@mcp.resource("tinydb://tables")
def get_tables_list() -> str:
    """Get list of all tables with metadata.

    Returns:
        JSON string with table information
    """
    try:
        tables = db_manager.get_all_tables()

        lines = [
            "=== TinyDB Tables ===",
            f"Total Tables: {len(tables)}",
            ""
        ]

        if tables:
            for table_name in tables:
                tbl = db_manager.get_table(table_name)
                doc_count = len(tbl)
                lines.append(f"Table: {table_name}")
                lines.append(f"  Documents: {doc_count}")

                # Show sample document structure if available
                if doc_count > 0:
                    sample = tbl.all()[0]
                    fields = list(sample.keys())
                    lines.append(f"  Sample fields: {', '.join(fields)}")

                lines.append("")
        else:
            lines.append("No tables found in database")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting tables list: {str(e)}"


@mcp.resource("tinydb://table/{table_name}")
def get_table_contents(table_name: str) -> str:
    """Get all documents from a specific table.

    Args:
        table_name: Name of the table

    Returns:
        JSON string with all documents from the table
    """
    try:
        # Check if table exists
        if table_name not in db_manager.get_all_tables():
            return f"Error: Table '{table_name}' does not exist"

        tbl = db_manager.get_table(table_name)
        documents = tbl.all()

        lines = [
            f"=== Table: {table_name} ===",
            f"Total Documents: {len(documents)}",
            ""
        ]

        if documents:
            for i, doc in enumerate(documents, 1):
                lines.append(f"Document {i}:")
                for key, value in doc.items():
                    lines.append(f"  {key}: {value}")
                lines.append("")
        else:
            lines.append("No documents in this table")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting table contents: {str(e)}"


# Entry point
if __name__ == "__main__":
    mcp.run(transport="stdio")
