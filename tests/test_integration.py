"""Integration tests for the MCP TinyDB Server.

These tests verify the end-to-end functionality of the MCP server,
including tool calls and resource access directly through the tool functions.
"""

import json
import os
import tempfile

import pytest
from pydantic import ValidationError

from src.mcp_tinydb_server import (
    delete_documents,
    get_database_stats,
    get_table_contents,
    get_tables_list,
    insert_document,
    list_tables,
    query_documents,
    update_documents,
)
from src.models import DocumentDelete, DocumentInsert, DocumentQuery, DocumentUpdate


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        db_path = f.name

    # Set environment variable for the test
    old_path = os.environ.get("TINYDB_PATH")
    os.environ["TINYDB_PATH"] = db_path

    # Need to reload the db_manager with new path
    from src.mcp_tinydb_server import db_manager

    db_manager.db_path = db_path
    db_manager._db = None  # Reset lazy-loaded database

    yield db_path

    # Cleanup
    db_manager.close()
    if os.path.exists(db_path):
        os.unlink(db_path)
    # Reset environment
    if old_path is not None:
        os.environ["TINYDB_PATH"] = old_path
    elif "TINYDB_PATH" in os.environ:
        del os.environ["TINYDB_PATH"]


class TestMCPIntegration:
    """Integration tests for MCP server operations."""

    def test_full_crud_workflow(self, temp_db):
        """Test complete CRUD workflow through MCP tools."""
        # Insert a document
        insert_result = insert_document(
            DocumentInsert(data={"name": "Alice", "age": 30, "city": "NYC"}, table="users")
        )
        assert insert_result.success is True
        assert insert_result.data is not None
        assert "document_id" in insert_result.data

        # Query the document
        query_result = query_documents(DocumentQuery(field="name", value="Alice", table="users"))
        assert query_result.success is True
        assert query_result.data is not None
        assert query_result.data["count"] == 1
        assert query_result.data["documents"][0]["age"] == 30

        # Update the document
        update_result = update_documents(
            DocumentUpdate(field="name", value="Alice", updates={"age": 31}, table="users")
        )
        assert update_result.success is True
        assert update_result.data is not None
        assert update_result.data["updated_count"] >= 1

        # Verify update
        verify_result = query_documents(DocumentQuery(field="name", value="Alice", table="users"))
        assert verify_result.data is not None
        assert verify_result.data["documents"][0]["age"] == 31

        # Delete the document
        delete_result = delete_documents(DocumentDelete(field="name", value="Alice", table="users"))
        assert delete_result.success is True
        assert delete_result.data is not None
        assert delete_result.data["deleted_count"] >= 1

        # Verify deletion
        final_result = query_documents(DocumentQuery(field="name", value="Alice", table="users"))
        assert final_result.data is not None
        assert final_result.data["count"] == 0

    def test_multi_table_operations(self, temp_db):
        """Test operations across multiple tables."""
        # Insert into users table
        insert_document(DocumentInsert(data={"name": "Alice"}, table="users"))

        # Insert into products table
        insert_document(DocumentInsert(data={"product": "Widget"}, table="products"))

        # List tables
        tables_result = list_tables()
        assert tables_result.success is True
        assert tables_result.data is not None
        assert "users" in tables_result.data["tables"]
        assert "products" in tables_result.data["tables"]

        # Query each table
        users_result = query_documents(DocumentQuery(table="users"))
        assert users_result.data is not None
        assert users_result.data["documents"][0]["name"] == "Alice"

        products_result = query_documents(DocumentQuery(table="products"))
        assert products_result.data is not None
        assert products_result.data["documents"][0]["product"] == "Widget"

    def test_resources_integration(self, temp_db):
        """Test MCP resources with actual data."""
        # Insert test data
        insert_document(DocumentInsert(data={"name": "Alice"}, table="users"))
        insert_document(DocumentInsert(data={"name": "Bob"}, table="users"))

        # Test stats resource (returns JSON)
        stats_content = get_database_stats()
        stats = json.loads(stats_content)
        assert "users" in stats["tables"]
        assert stats["tables"]["users"]["document_count"] == 2

        # Test tables resource (returns JSON)
        tables_content = get_tables_list()
        tables_data = json.loads(tables_content)
        table_names = [t["name"] for t in tables_data["tables"]]
        assert "users" in table_names

        # Test table-specific resource (returns formatted text)
        table_content = get_table_contents(table_name="users")
        assert "alice" in table_content.lower()
        assert "bob" in table_content.lower()

    def test_error_handling_integration(self, temp_db):
        """Test error handling."""
        # Try to insert invalid data - Pydantic will raise validation error
        with pytest.raises(ValidationError):
            DocumentInsert(data="not a dict")  # type: ignore

        # Try to update with invalid updates - Pydantic will raise validation error
        with pytest.raises(ValidationError):
            DocumentUpdate(field="name", value="Alice", updates="not a dict")  # type: ignore

    def test_database_persistence(self, temp_db):
        """Test that data persists in the database file."""
        # Insert data
        insert_document(DocumentInsert(data={"name": "Alice"}, table="users"))

        # Verify file exists and has content
        assert os.path.exists(temp_db)
        assert os.path.getsize(temp_db) > 0

        # Read file to verify JSON structure
        with open(temp_db) as f:
            content = f.read()
            assert "Alice" in content

    def test_empty_database_operations(self, temp_db):
        """Test operations on empty database."""
        # Query empty table
        result = query_documents(DocumentQuery(table="users"))
        assert result.success is True
        assert result.data is not None
        assert result.data["count"] == 0

        # List tables in empty database
        result = list_tables()
        assert result.success is True
        assert result.data is not None

        # Get stats on empty database
        stats_content = get_database_stats()
        stats = json.loads(stats_content)
        assert stats["total_tables"] == 0

    def test_bulk_operations(self, temp_db):
        """Test inserting and querying multiple documents."""
        # Insert multiple documents
        for i in range(10):
            insert_document(DocumentInsert(data={"name": f"User{i}", "index": i}, table="users"))

        # Query all documents
        result = query_documents(DocumentQuery(table="users"))
        assert result.data is not None
        assert result.data["count"] == 10

        # Update multiple documents
        update_result = update_documents(
            DocumentUpdate(field="index", value=5, updates={"updated": True}, table="users")
        )
        assert update_result.data is not None
        assert update_result.data["updated_count"] == 1  # Should update 1 document
