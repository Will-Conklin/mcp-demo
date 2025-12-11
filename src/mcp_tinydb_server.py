"""MCP Server for TinyDB document database operations."""

import os
from typing import TYPE_CHECKING, Any

import logfire
from mcp.server.fastmcp import FastMCP
from tinydb import Query, TinyDB

from src.config import configure_logging, settings
from src.models import (
    DatabaseStats,
    DocumentDelete,
    DocumentInsert,
    DocumentQuery,
    DocumentUpdate,
    OperationResult,
    TableStats,
)

if TYPE_CHECKING:
    from tinydb.table import Table

# Configure logging on module import
configure_logging()


class TinyDBManager:
    """Manager class for TinyDB database operations."""

    def __init__(self, db_path: str = "tinydb_data.json") -> None:
        """Initialize the TinyDB manager.

        Args:
            db_path: Path to the TinyDB database file
        """
        self.db_path = db_path
        self._db: TinyDB | None = None

    @property
    def db(self) -> TinyDB:
        """Lazy initialization of database.

        Returns:
            TinyDB instance
        """
        if self._db is None:
            self._db = TinyDB(self.db_path)
        return self._db

    def get_table(self, table_name: str) -> "Table":
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
        tables: dict[str, dict[str, int]] = {}

        # Get document count per table
        for table_name in self.db.tables():
            table = self.get_table(table_name)
            tables[table_name] = {"document_count": len(table)}

        stats: dict[str, Any] = {
            "database_path": os.path.abspath(self.db_path),
            "total_tables": len(self.db.tables()),
            "tables": tables,
        }

        # Get file size if database file exists
        if os.path.exists(self.db_path):
            stats["database_size_bytes"] = os.path.getsize(self.db_path)
        else:
            stats["database_size_bytes"] = 0

        return stats

    def close(self) -> None:
        """Close database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None


# Initialize FastMCP server
mcp = FastMCP(
    name=settings.server_name,
    instructions="A Model Context Protocol server for TinyDB operations. "
    "Provides tools for document insertion, querying, updating, "
    "and deletion, plus resources for database statistics.",
)

# Initialize database manager with settings
db_manager = TinyDBManager(db_path=str(settings.tinydb_path))
logfire.info("Database manager initialized", db_path=str(settings.tinydb_path))


# Tools
@mcp.tool()
def insert_document(doc: DocumentInsert) -> OperationResult:
    """Insert a document into TinyDB.

    Args:
        doc: DocumentInsert model containing data and table name

    Returns:
        OperationResult with the inserted document ID
    """
    try:
        with logfire.span("insert_document", table=doc.table, data_keys=list(doc.data.keys())):
            # Get table and insert document
            tbl = db_manager.get_table(doc.table)
            doc_id = tbl.insert(doc.data)

            logfire.info("Document inserted", doc_id=doc_id, table=doc.table)
            return OperationResult(
                success=True,
                message="Document inserted successfully",
                data={"document_id": doc_id, "table": doc.table},
            )
    except Exception as e:
        logfire.error("Insert failed", error=str(e), table=doc.table)
        return OperationResult(success=False, message="Failed to insert document", error=str(e))


@mcp.tool()
def query_documents(query: DocumentQuery) -> OperationResult:
    """Query documents from TinyDB.

    Args:
        query: DocumentQuery model with optional field/value filter and table name

    Returns:
        OperationResult with list of matching documents
    """
    try:
        tbl = db_manager.get_table(query.table)

        # If no field/value, return all documents
        if query.field is None:
            documents = tbl.all()
        else:
            # Search using equality query
            q = Query()
            documents = tbl.search(q[query.field] == query.value)

        return OperationResult(
            success=True,
            message=f"Found {len(documents)} document(s)",
            data={"count": len(documents), "documents": documents, "table": query.table},
        )
    except Exception as e:
        return OperationResult(success=False, message="Failed to query documents", error=str(e))


@mcp.tool()
def update_documents(update: DocumentUpdate) -> OperationResult:
    """Update documents matching criteria.

    Args:
        update: DocumentUpdate model with field, value, updates, and table name

    Returns:
        OperationResult with count of updated documents
    """
    try:
        tbl = db_manager.get_table(update.table)
        q = Query()

        # Update documents matching the criteria
        doc_ids = tbl.update(update.updates, q[update.field] == update.value)

        updated_count = len(doc_ids) if isinstance(doc_ids, list) else (1 if doc_ids else 0)

        return OperationResult(
            success=True,
            message=f"Updated {updated_count} document(s)",
            data={"updated_count": updated_count, "table": update.table},
        )
    except Exception as e:
        return OperationResult(success=False, message="Failed to update documents", error=str(e))


@mcp.tool()
def delete_documents(delete: DocumentDelete) -> OperationResult:
    """Delete documents from TinyDB matching specific criteria.

    Args:
        delete: DocumentDelete model with field, value, and table name

    Returns:
        OperationResult with count of deleted documents
    """
    try:
        tbl = db_manager.get_table(delete.table)
        q = Query()
        doc_ids = tbl.remove(q[delete.field] == delete.value)

        deleted_count = len(doc_ids) if isinstance(doc_ids, list) else (1 if doc_ids else 0)

        return OperationResult(
            success=True,
            message=f"Deleted {deleted_count} document(s)",
            data={"deleted_count": deleted_count, "table": delete.table},
        )
    except Exception as e:
        return OperationResult(success=False, message="Failed to delete documents", error=str(e))


@mcp.tool()
def list_tables() -> OperationResult:
    """List all available tables/collections in the database.

    Returns:
        OperationResult with list of table names
    """
    try:
        tables = db_manager.get_all_tables()
        return OperationResult(
            success=True,
            message=f"Found {len(tables)} table(s)",
            data={"tables": tables, "count": len(tables)},
        )
    except Exception as e:
        return OperationResult(success=False, message="Failed to list tables", error=str(e))


# Resources
@mcp.resource("tinydb://stats")
def get_database_stats() -> str:
    """Get database statistics including document counts per table.

    Returns:
        JSON string with database statistics
    """
    try:
        stats = db_manager.get_stats()

        # Create DatabaseStats model from stats dict
        stats_model = DatabaseStats(
            database_path=stats["database_path"],
            database_size_bytes=stats["database_size_bytes"],
            total_tables=stats["total_tables"],
            tables=stats["tables"],
        )

        # Return JSON string of the model
        return stats_model.model_dump_json(indent=2)
    except Exception as e:
        return f"Error getting database statistics: {str(e)}"


@mcp.resource("tinydb://tables")
def get_tables_list() -> str:
    """Get list of all tables with metadata.

    Returns:
        JSON string with table information
    """
    try:
        import json

        tables = db_manager.get_all_tables()
        table_stats_list: list[TableStats] = []

        for table_name in tables:
            tbl = db_manager.get_table(table_name)
            doc_count = len(tbl)

            # Get sample fields if documents exist
            sample_fields: list[str] = []
            if doc_count > 0:
                sample = tbl.all()[0]
                sample_fields = list(sample.keys())

            table_stats_list.append(
                TableStats(name=table_name, document_count=doc_count, sample_fields=sample_fields)
            )

        # Return JSON string with array of TableStats
        return json.dumps({"tables": [stat.model_dump() for stat in table_stats_list]}, indent=2)
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

        lines = [f"=== Table: {table_name} ===", f"Total Documents: {len(documents)}", ""]

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
