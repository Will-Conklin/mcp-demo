"""Tests for MCP tools."""

import os
import tempfile

import pytest

from src.mcp_tinydb_server import (
    db_manager,
    delete_documents,
    insert_document,
    list_tables,
    query_documents,
    update_documents,
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


class TestInsertDocument:
    """Tests for insert_document tool."""

    def test_insert_valid_document(self):
        """Test inserting a valid document."""
        result = insert_document({"name": "Alice", "age": 30})

        assert result["success"] is True
        assert "document_id" in result
        assert result["table"] == "default"
        assert isinstance(result["document_id"], int)

    def test_insert_to_custom_table(self):
        """Test inserting into a custom table."""
        result = insert_document({"product": "Widget"}, table="products")

        assert result["success"] is True
        assert result["table"] == "products"

    def test_insert_invalid_data_type(self):
        """Test inserting non-dictionary data."""
        result = insert_document("not a dict")

        assert result["success"] is False
        assert "error" in result
        assert "must be a dictionary" in result["error"].lower()

    def test_insert_empty_document(self):
        """Test inserting an empty document."""
        result = insert_document({})

        assert result["success"] is True
        assert "document_id" in result


class TestQueryDocuments:
    """Tests for query_documents tool."""

    def test_query_all_documents(self):
        """Test querying all documents in a table."""
        # Insert test data
        insert_document({"name": "Alice", "age": 30})
        insert_document({"name": "Bob", "age": 25})

        result = query_documents()

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["documents"]) == 2

    def test_query_by_field_value(self):
        """Test querying documents by field and value."""
        # Insert test data
        insert_document({"name": "Alice", "city": "NYC"})
        insert_document({"name": "Bob", "city": "LA"})
        insert_document({"name": "Charlie", "city": "NYC"})

        result = query_documents(field="city", value="NYC")

        assert result["success"] is True
        assert result["count"] == 2
        assert all(doc["city"] == "NYC" for doc in result["documents"])

    def test_query_no_matches(self):
        """Test querying with no matching documents."""
        insert_document({"name": "Alice", "age": 30})

        result = query_documents(field="name", value="Bob")

        assert result["success"] is True
        assert result["count"] == 0
        assert result["documents"] == []

    def test_query_field_without_value(self):
        """Test querying with field but no value."""
        result = query_documents(field="name")

        assert result["success"] is False
        assert "error" in result

    def test_query_empty_table(self):
        """Test querying an empty table."""
        result = query_documents()

        assert result["success"] is True
        assert result["count"] == 0
        assert result["documents"] == []

    def test_query_custom_table(self):
        """Test querying from a custom table."""
        insert_document({"product": "Widget"}, table="products")

        result = query_documents(table="products")

        assert result["success"] is True
        assert result["count"] == 1


class TestUpdateDocuments:
    """Tests for update_documents tool."""

    def test_update_single_document(self):
        """Test updating a single document."""
        insert_document({"name": "Alice", "age": 30})

        result = update_documents(field="name", value="Alice", updates={"age": 31})

        assert result["success"] is True
        assert result["updated_count"] >= 1

        # Verify update
        query_result = query_documents(field="name", value="Alice")
        assert query_result["documents"][0]["age"] == 31

    def test_update_multiple_documents(self):
        """Test updating multiple documents."""
        insert_document({"city": "NYC", "status": "active"})
        insert_document({"city": "NYC", "status": "active"})

        result = update_documents(field="city", value="NYC", updates={"status": "inactive"})

        assert result["success"] is True
        assert result["updated_count"] >= 2

    def test_update_no_matches(self):
        """Test updating with no matching documents."""
        insert_document({"name": "Alice", "age": 30})

        result = update_documents(field="name", value="Bob", updates={"age": 25})

        assert result["success"] is True
        assert result["updated_count"] == 0

    def test_update_invalid_updates_type(self):
        """Test updating with non-dictionary updates."""
        result = update_documents(field="name", value="Alice", updates="not a dict")

        assert result["success"] is False
        assert "error" in result

    def test_update_add_new_field(self):
        """Test adding a new field via update."""
        insert_document({"name": "Alice"})

        result = update_documents(
            field="name", value="Alice", updates={"email": "alice@example.com"}
        )

        assert result["success"] is True

        # Verify new field was added
        query_result = query_documents(field="name", value="Alice")
        assert "email" in query_result["documents"][0]


class TestDeleteDocuments:
    """Tests for delete_documents tool."""

    def test_delete_by_field_value(self):
        """Test deleting documents by field and value."""
        insert_document({"name": "Alice", "age": 30})
        insert_document({"name": "Bob", "age": 25})

        result = delete_documents(field="name", value="Alice")

        assert result["success"] is True
        assert result["deleted_count"] >= 1

        # Verify deletion
        query_result = query_documents()
        assert query_result["count"] == 1
        assert query_result["documents"][0]["name"] == "Bob"

    def test_delete_multiple_documents(self):
        """Test deleting multiple matching documents."""
        insert_document({"city": "NYC", "name": "Alice"})
        insert_document({"city": "NYC", "name": "Bob"})
        insert_document({"city": "LA", "name": "Charlie"})

        result = delete_documents(field="city", value="NYC")

        assert result["success"] is True
        assert result["deleted_count"] >= 2

    def test_delete_no_matches(self):
        """Test deleting with no matching documents."""
        insert_document({"name": "Alice"})

        result = delete_documents(field="name", value="Bob")

        assert result["success"] is True
        assert result["deleted_count"] == 0


class TestListTables:
    """Tests for list_tables tool."""

    def test_list_tables_empty_db(self):
        """Test listing tables in an empty database."""
        result = list_tables()

        assert result["success"] is True
        assert result["count"] == 0
        assert result["tables"] == []

    def test_list_tables_with_data(self):
        """Test listing tables after creating some."""
        insert_document({"data": "test1"}, table="table1")
        insert_document({"data": "test2"}, table="table2")
        insert_document({"data": "test3"}, table="table3")

        result = list_tables()

        assert result["success"] is True
        assert result["count"] == 3
        assert "table1" in result["tables"]
        assert "table2" in result["tables"]
        assert "table3" in result["tables"]

    def test_list_tables_includes_default(self):
        """Test that default table is included when used."""
        insert_document({"data": "test"})  # Uses default table

        result = list_tables()

        assert result["success"] is True
        assert "default" in result["tables"] or "_default" in result["tables"]
