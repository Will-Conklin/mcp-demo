"""Integration tests for the MCP TinyDB Server.

These tests verify the end-to-end functionality of the MCP server,
including tool calls and resource access directly through the tool functions.
"""

import os
import tempfile

import pytest

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
            data={"name": "Alice", "age": 30, "city": "NYC"}, table="users"
        )
        result_str = str(insert_result)
        assert "success" in result_str.lower()
        assert "doc_id" in result_str.lower() or "id" in result_str.lower()

        # Query the document
        query_result = query_documents(field="name", value="Alice", table="users")
        result_str = str(query_result)
        assert "alice" in result_str.lower()
        assert "30" in result_str

        # Update the document
        update_result = update_documents(
            field="name", value="Alice", updates={"age": 31}, table="users"
        )
        result_str = str(update_result)
        assert "success" in result_str.lower() or "1" in result_str

        # Verify update
        verify_result = query_documents(field="name", value="Alice", table="users")
        result_str = str(verify_result)
        assert "31" in result_str

        # Delete the document
        delete_result = delete_documents(field="name", value="Alice", table="users")
        result_str = str(delete_result)
        assert "success" in result_str.lower() or "1" in result_str

        # Verify deletion
        final_result = query_documents(field="name", value="Alice", table="users")
        result_str = str(final_result)
        assert "0" in result_str or "count': 0" in result_str

    def test_multi_table_operations(self, temp_db):
        """Test operations across multiple tables."""
        # Insert into users table
        insert_document(data={"name": "Alice"}, table="users")

        # Insert into products table
        insert_document(data={"product": "Widget"}, table="products")

        # List tables
        tables_result = list_tables()
        result_str = str(tables_result)
        assert "users" in result_str.lower()
        assert "products" in result_str.lower()

        # Query each table
        users_result = query_documents(table="users")
        result_str = str(users_result)
        assert "alice" in result_str.lower()

        products_result = query_documents(table="products")
        result_str = str(products_result)
        assert "widget" in result_str.lower()

    def test_resources_integration(self, temp_db):
        """Test MCP resources with actual data."""
        # Insert test data
        insert_document(data={"name": "Alice"}, table="users")
        insert_document(data={"name": "Bob"}, table="users")

        # Test stats resource
        stats_content = get_database_stats()
        assert "users" in stats_content.lower()
        assert "2" in stats_content  # 2 documents

        # Test tables resource
        tables_content = get_tables_list()
        assert "users" in tables_content.lower()

        # Test table-specific resource
        table_content = get_table_contents(table_name="users")
        assert "alice" in table_content.lower()
        assert "bob" in table_content.lower()

    def test_error_handling_integration(self, temp_db):
        """Test error handling."""
        # Try to insert invalid data - should contain error message
        error_result = insert_document(data="not a dict", table="users")
        result_str = str(error_result)
        assert "error" in result_str.lower() or "must be" in result_str.lower()

        # Try to update with invalid updates
        error_result = update_documents(
            field="name", value="Alice", updates="not a dict", table="users"
        )
        result_str = str(error_result)
        assert "error" in result_str.lower() or "must be" in result_str.lower()

    def test_database_persistence(self, temp_db):
        """Test that data persists in the database file."""
        # Insert data
        insert_document(data={"name": "Alice"}, table="users")

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
        result = query_documents(table="users")
        result_str = str(result)
        assert "0" in result_str or "no documents" in result_str.lower()

        # List tables in empty database
        result = list_tables()
        # Should return something (dict or string)
        assert result is not None

        # Get stats on empty database
        stats_content = get_database_stats()
        result_str = str(stats_content)
        assert "0" in result_str

    def test_bulk_operations(self, temp_db):
        """Test inserting and querying multiple documents."""
        # Insert multiple documents
        for i in range(10):
            insert_document(data={"name": f"User{i}", "index": i}, table="users")

        # Query all documents
        result = query_documents(table="users")
        result_str = str(result)
        # Verify we got all 10
        assert "10" in result_str

        # Update multiple documents
        update_result = update_documents(
            field="index", value=5, updates={"updated": True}, table="users"
        )
        result_str = str(update_result)
        assert "1" in result_str  # Should update 1 document
