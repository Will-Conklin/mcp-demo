"""Tests for MCP resources."""

import os
import tempfile

import pytest

from src.mcp_tinydb_server import (
    db_manager,
    get_database_stats,
    get_table_contents,
    get_tables_list,
    insert_document,
)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up a fresh test database for each test."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_db_path = f.name

    # Replace the db_manager's database path
    original_path = db_manager.db_path
    db_manager.db_path = test_db_path
    db_manager.close()  # Close any existing connection

    yield

    # Cleanup
    db_manager.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Restore original path
    db_manager.db_path = original_path


class TestDatabaseStatsResource:
    """Tests for get_database_stats resource."""

    def test_stats_empty_database(self):
        """Test getting stats from an empty database."""
        stats = get_database_stats()

        assert isinstance(stats, str)
        assert "Database Path" in stats
        assert "Database Size" in stats
        assert "Total Tables: 0" in stats

    def test_stats_with_data(self):
        """Test getting stats from a database with data."""
        # Add test data
        insert_document({"name": "Alice"}, table="users")
        insert_document({"name": "Bob"}, table="users")
        insert_document({"product": "Widget"}, table="products")

        stats = get_database_stats()

        assert isinstance(stats, str)
        assert "Total Tables: 2" in stats
        assert "users" in stats
        assert "products" in stats
        assert "documents" in stats.lower()

    def test_stats_shows_document_counts(self):
        """Test that stats show accurate document counts."""
        insert_document({"data": "test1"}, table="table1")
        insert_document({"data": "test2"}, table="table1")
        insert_document({"data": "test3"}, table="table1")

        stats = get_database_stats()

        assert "table1" in stats
        assert "3 documents" in stats

    def test_stats_shows_file_size(self):
        """Test that stats include file size."""
        insert_document({"data": "test"})

        stats = get_database_stats()

        assert "bytes" in stats
        # File size should be greater than 0 after inserting data
        assert "0 bytes" not in stats or "Database Size: 0 bytes" not in stats


class TestTablesListResource:
    """Tests for get_tables_list resource."""

    def test_tables_list_empty_database(self):
        """Test getting table list from empty database."""
        tables_list = get_tables_list()

        assert isinstance(tables_list, str)
        assert "Total Tables: 0" in tables_list
        assert "No tables found" in tables_list

    def test_tables_list_with_tables(self):
        """Test getting table list with multiple tables."""
        insert_document({"name": "Alice"}, table="users")
        insert_document({"product": "Widget"}, table="products")
        insert_document({"order": "123"}, table="orders")

        tables_list = get_tables_list()

        assert "Total Tables: 3" in tables_list
        assert "users" in tables_list
        assert "products" in tables_list
        assert "orders" in tables_list

    def test_tables_list_shows_document_counts(self):
        """Test that table list shows document counts."""
        insert_document({"data": "test1"}, table="test_table")
        insert_document({"data": "test2"}, table="test_table")

        tables_list = get_tables_list()

        assert "test_table" in tables_list
        assert "Documents: 2" in tables_list

    def test_tables_list_shows_sample_fields(self):
        """Test that table list shows sample fields from documents."""
        insert_document({"name": "Alice", "age": 30, "city": "NYC"}, table="users")

        tables_list = get_tables_list()

        assert "Sample fields" in tables_list
        # At least some of the fields should be shown
        assert "name" in tables_list or "age" in tables_list or "city" in tables_list


class TestTableContentsResource:
    """Tests for get_table_contents resource."""

    def test_table_contents_empty_table(self):
        """Test getting contents of an empty table."""
        # Create an empty table by querying it
        insert_document({"data": "temp"}, table="test_table")
        db_manager.get_table("test_table").truncate()

        contents = get_table_contents("test_table")

        assert isinstance(contents, str)
        assert "test_table" in contents
        assert "Total Documents: 0" in contents
        assert "No documents" in contents

    def test_table_contents_with_data(self):
        """Test getting contents of a table with data."""
        insert_document({"name": "Alice", "age": 30}, table="users")
        insert_document({"name": "Bob", "age": 25}, table="users")

        contents = get_table_contents("users")

        assert "Table: users" in contents
        assert "Total Documents: 2" in contents
        assert "Alice" in contents
        assert "Bob" in contents
        assert "30" in contents or "age: 30" in contents
        assert "25" in contents or "age: 25" in contents

    def test_table_contents_nonexistent_table(self):
        """Test getting contents of a non-existent table."""
        contents = get_table_contents("nonexistent_table")

        assert "Error" in contents or "does not exist" in contents

    def test_table_contents_shows_all_fields(self):
        """Test that all document fields are shown."""
        insert_document(
            {"name": "Alice", "age": 30, "city": "NYC", "email": "alice@example.com"}, table="users"
        )

        contents = get_table_contents("users")

        assert "name" in contents
        assert "age" in contents
        assert "city" in contents
        assert "email" in contents
        assert "Alice" in contents
        assert "NYC" in contents

    def test_table_contents_multiple_documents(self):
        """Test that all documents are shown."""
        for i in range(5):
            insert_document({"id": i, "value": f"test{i}"}, table="data")

        contents = get_table_contents("data")

        assert "Total Documents: 5" in contents
        # Check that at least some of the documents are shown
        assert "test0" in contents or "test1" in contents
        assert "Document" in contents  # Document labels

    def test_table_contents_formatting(self):
        """Test that table contents are well-formatted."""
        insert_document({"key": "value"}, table="test")

        contents = get_table_contents("test")

        # Check for proper formatting elements
        assert "===" in contents  # Header separator
        assert "Document 1:" in contents  # Document numbering
        assert "key:" in contents or "key :" in contents  # Field formatting
