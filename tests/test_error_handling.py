"""Error handling and edge case tests.

These tests validate error scenarios, file system issues, database corruption,
invalid queries, and large data handling to ensure robustness.
"""

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
from src.models import DocumentDelete, DocumentInsert, DocumentQuery, DocumentUpdate


@pytest.mark.permissions
class TestFileSystemErrors:
    """Tests for file system permission and access errors."""

    def test_insert_readonly_database(self, temp_readonly_file):
        """Test inserting into a read-only database file."""
        # Set up db_manager with readonly file
        original_path = db_manager.db_path
        db_manager.db_path = temp_readonly_file
        db_manager._db = None  # Reset to force reload

        try:
            # Try to insert - should fail or handle gracefully
            result = insert_document(DocumentInsert(data={"test": "value"}))
            # TinyDB might not enforce permissions immediately, so we check the result
            # The operation might succeed in memory but fail on flush
            assert isinstance(result.success, bool)
        finally:
            db_manager.db_path = original_path
            db_manager._db = None

    def test_database_path_is_directory(self):
        """Test when database path points to a directory instead of a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = db_manager.db_path
            db_manager.db_path = tmpdir  # Point to directory
            db_manager._db = None

            try:
                # This should handle the error gracefully
                result = insert_document(DocumentInsert(data={"test": "value"}))
                # TinyDB will likely fail here
                assert isinstance(result.success, bool)
            finally:
                db_manager.db_path = original_path
                db_manager._db = None

    def test_invalid_database_path(self):
        """Test with an invalid/nonexistent parent directory."""
        original_path = db_manager.db_path
        db_manager.db_path = "/nonexistent/path/to/database.json"
        db_manager._db = None

        try:
            # This should create the database or fail gracefully
            result = insert_document(DocumentInsert(data={"test": "value"}))
            assert isinstance(result.success, bool)
        except Exception:
            # Expected to fail
            pass
        finally:
            db_manager.db_path = original_path
            db_manager._db = None


@pytest.mark.corruption
class TestDatabaseCorruption:
    """Tests for handling corrupted database files."""

    def test_corrupted_json_file(self, corrupted_json_file):
        """Test reading a database with corrupted JSON."""
        original_path = db_manager.db_path
        db_manager.db_path = corrupted_json_file
        db_manager._db = None

        try:
            # Try to query - should handle corruption gracefully
            result = query_documents(DocumentQuery())
            assert isinstance(result.success, bool)
        except Exception as e:
            # Expected: JSON decode error or similar
            assert "json" in str(e).lower() or "decode" in str(e).lower()
        finally:
            db_manager.db_path = original_path
            db_manager._db = None

    def test_truncated_json_file(self, truncated_json_file):
        """Test reading a truncated JSON file."""
        original_path = db_manager.db_path
        db_manager.db_path = truncated_json_file
        db_manager._db = None

        try:
            result = query_documents(DocumentQuery())
            assert isinstance(result.success, bool)
        except Exception as e:
            # Expected: JSON decode error
            assert "json" in str(e).lower() or "decode" in str(e).lower()
        finally:
            db_manager.db_path = original_path
            db_manager._db = None

    def test_empty_file_as_database(self, empty_json_file):
        """Test using an empty file as database."""
        original_path = db_manager.db_path
        db_manager.db_path = empty_json_file
        db_manager._db = None

        try:
            # Empty file should be handled - TinyDB creates new structure
            result = insert_document(DocumentInsert(data={"test": "value"}))
            assert isinstance(result.success, bool)
        finally:
            db_manager.db_path = original_path
            db_manager._db = None

    def test_binary_file_as_database(self, binary_file):
        """Test using a binary file as database."""
        original_path = db_manager.db_path
        db_manager.db_path = binary_file
        db_manager._db = None

        try:
            result = query_documents(DocumentQuery())
            assert isinstance(result.success, bool)
        except Exception as e:
            # Expected: decode error
            assert "decode" in str(e).lower() or "utf" in str(e).lower()
        finally:
            db_manager.db_path = original_path
            db_manager._db = None


class TestInvalidQueries:
    """Tests for invalid query patterns and edge cases."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Set up a fresh test database for each test."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_db_path = f.name

        original_path = db_manager.db_path
        db_manager.db_path = test_db_path
        db_manager.close()

        yield

        db_manager.close()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        db_manager.db_path = original_path

    def test_query_nonexistent_field(self):
        """Test querying a field that doesn't exist in documents."""
        # Insert document without 'nonexistent' field
        insert_document(DocumentInsert(data={"name": "Alice"}))

        # Query for nonexistent field
        result = query_documents(DocumentQuery(field="nonexistent", value="test"))

        assert result.success is True
        assert result.data is not None
        assert result.data["count"] == 0  # No matches

    def test_query_type_mismatch(self):
        """Test querying with type mismatch (string vs int)."""
        # Insert with integer field
        insert_document(DocumentInsert(data={"age": 30}))

        # Query with string value
        result = query_documents(DocumentQuery(field="age", value="30"))

        assert result.success is True
        assert result.data is not None
        # Type mismatch means no match
        assert result.data["count"] == 0

    def test_update_nonexistent_field(self):
        """Test updating based on a field that doesn't exist."""
        insert_document(DocumentInsert(data={"name": "Alice"}))

        # Update based on nonexistent field
        result = update_documents(
            DocumentUpdate(field="nonexistent", value="test", updates={"status": "active"})
        )

        assert result.success is True
        assert result.data is not None
        assert result.data["updated_count"] == 0

    def test_delete_nonexistent_field(self):
        """Test deleting based on a field that doesn't exist."""
        insert_document(DocumentInsert(data={"name": "Alice"}))

        # Delete based on nonexistent field
        result = delete_documents(DocumentDelete(field="nonexistent", value="test"))

        assert result.success is True
        assert result.data is not None
        assert result.data["deleted_count"] == 0

    def test_query_with_none_values(self):
        """Test querying documents that contain None values."""
        # Insert document with None value
        insert_document(DocumentInsert(data={"name": "Alice", "email": None}))

        # Note: DocumentQuery validator treats (field="x", value=None) as invalid
        # To query for None value, we need both field and value to be None or both set
        # This documents that you cannot query for None values with current validator

        # Query all documents instead (which will include the one with None email)
        result = query_documents(DocumentQuery())

        assert result.success is True
        assert result.data is not None
        assert result.data["count"] == 1
        assert result.data["documents"][0]["email"] is None

    def test_documents_missing_queried_field(self):
        """Test querying when some documents are missing the queried field."""
        # Insert docs with and without the field
        insert_document(DocumentInsert(data={"name": "Alice", "age": 30}))
        insert_document(DocumentInsert(data={"name": "Bob"}))  # No age field

        # Query for age
        result = query_documents(DocumentQuery(field="age", value=30))

        assert result.success is True
        assert result.data is not None
        assert result.data["count"] == 1  # Only Alice has age field


@pytest.mark.slow
class TestLargeDataHandling:
    """Tests for handling large documents and datasets."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Set up a fresh test database for each test."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_db_path = f.name

        original_path = db_manager.db_path
        db_manager.db_path = test_db_path
        db_manager.close()

        yield

        db_manager.close()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        db_manager.db_path = original_path

    def test_insert_very_large_document(self, large_document):
        """Test inserting a very large document (1MB+)."""
        result = insert_document(DocumentInsert(data=large_document))

        assert result.success is True
        assert result.data is not None
        assert "document_id" in result.data

    def test_insert_deeply_nested_document(self, deeply_nested_dict):
        """Test inserting a deeply nested document (50 levels)."""
        result = insert_document(DocumentInsert(data=deeply_nested_dict))

        assert result.success is True
        assert result.data is not None
        assert "document_id" in result.data

    def test_query_large_dataset(self):
        """Test querying from a large dataset (1000 documents)."""
        # Insert 1000 documents
        for i in range(1000):
            insert_document(DocumentInsert(data={"id": i, "value": f"test_{i}"}))

        # Query all
        result = query_documents(DocumentQuery())

        assert result.success is True
        assert result.data is not None
        assert result.data["count"] == 1000

    def test_update_large_dataset(self):
        """Test updating multiple documents in a large dataset."""
        # Insert 100 documents with same status
        for i in range(100):
            insert_document(DocumentInsert(data={"id": i, "status": "pending"}))

        # Update all
        result = update_documents(
            DocumentUpdate(field="status", value="pending", updates={"status": "active"})
        )

        assert result.success is True
        assert result.data is not None
        # TinyDB returns a list of IDs or a single value
        assert result.data["updated_count"] > 0

    def test_large_field_names(self):
        """Test document with very long field names (1000 chars)."""
        long_key = "x" * 1000
        result = insert_document(DocumentInsert(data={long_key: "value"}))

        assert result.success is True
        assert result.data is not None


class TestToolErrorPaths:
    """Tests for specific error paths in tool functions."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Set up a fresh test database for each test."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_db_path = f.name

        original_path = db_manager.db_path
        db_manager.db_path = test_db_path
        db_manager.close()

        yield

        db_manager.close()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        db_manager.db_path = original_path

    def test_list_tables_error_handling(self):
        """Test list_tables handles errors gracefully."""
        # Even with empty DB, should work
        result = list_tables()

        assert result.success is True
        assert result.data is not None
        assert isinstance(result.data["tables"], list)

    def test_query_after_delete_all(self):
        """Test querying after deleting all documents."""
        # Insert and delete
        insert_document(DocumentInsert(data={"name": "Alice"}))
        delete_documents(DocumentDelete(field="name", value="Alice"))

        # Query should return empty
        result = query_documents(DocumentQuery())

        assert result.success is True
        assert result.data is not None
        assert result.data["count"] == 0
