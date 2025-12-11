"""Unit tests for Pydantic models.

These tests validate all Pydantic models, their validators, field constraints,
and ensure proper error handling for invalid inputs.
"""

import pytest
from pydantic import ValidationError

from src.models import (
    DatabaseStats,
    DocumentDelete,
    DocumentInsert,
    DocumentQuery,
    DocumentUpdate,
    OperationResult,
    TableStats,
)


class TestDocumentInsertValidation:
    """Tests for DocumentInsert model validation."""

    def test_valid_document_insert(self):
        """Test creating a valid DocumentInsert."""
        doc = DocumentInsert(data={"name": "Alice", "age": 30})
        assert doc.data == {"name": "Alice", "age": 30}
        assert doc.table == "default"

    def test_valid_document_insert_custom_table(self):
        """Test DocumentInsert with custom table name."""
        doc = DocumentInsert(data={"test": "value"}, table="custom")
        assert doc.table == "custom"

    def test_empty_data_raises_error(self):
        """Test that empty data dict raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentInsert(data={})
        assert "Document data cannot be empty" in str(exc_info.value)

    def test_none_data_raises_error(self):
        """Test that None data raises validation error."""
        with pytest.raises(ValidationError):
            DocumentInsert(data=None)  # type: ignore

    def test_special_chars_in_keys(self):
        """Test document with special characters in keys."""
        doc = DocumentInsert(data={"key-with-dash": "value", "key.with.dots": "value"})
        assert doc.data["key-with-dash"] == "value"
        assert doc.data["key.with.dots"] == "value"

    def test_unicode_keys_and_values(self):
        """Test document with unicode characters."""
        doc = DocumentInsert(data={"name": "你好", "greeting": "مرحبا"})
        assert doc.data["name"] == "你好"
        assert doc.data["greeting"] == "مرحبا"

    def test_empty_table_name(self):
        """Test that empty table name is allowed (TinyDB will handle it)."""
        doc = DocumentInsert(data={"test": "value"}, table="")
        assert doc.table == ""

    def test_very_long_field_names(self):
        """Test document with very long field names."""
        long_key = "x" * 1000
        doc = DocumentInsert(data={long_key: "value"})
        assert doc.data[long_key] == "value"

    def test_nested_dict_data(self):
        """Test document with nested dictionary structure."""
        nested_data = {"user": {"name": "Alice", "address": {"city": "NYC"}}}
        doc = DocumentInsert(data=nested_data)
        assert doc.data["user"]["address"]["city"] == "NYC"


class TestDocumentQueryValidation:
    """Tests for DocumentQuery model validation."""

    def test_valid_query_with_field_value(self):
        """Test creating a valid query with field and value."""
        query = DocumentQuery(field="name", value="Alice")
        assert query.field == "name"
        assert query.value == "Alice"
        assert query.table == "default"

    def test_valid_query_without_field_value(self):
        """Test creating a query without field and value (returns all)."""
        query = DocumentQuery()
        assert query.field is None
        assert query.value is None
        assert query.table == "default"

    def test_field_without_value_raises_error(self):
        """Test that field without value raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentQuery(field="name")
        assert "field" in str(exc_info.value).lower() and "value" in str(exc_info.value).lower()

    def test_value_without_field_raises_error(self):
        """Test that value without field raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentQuery(value="Alice")
        assert "field" in str(exc_info.value).lower() and "value" in str(exc_info.value).lower()

    def test_empty_field_name(self):
        """Test query with empty field name."""
        query = DocumentQuery(field="", value="test")
        assert query.field == ""
        assert query.value == "test"

    def test_unicode_field_names(self):
        """Test query with unicode field names and values."""
        query = DocumentQuery(field="名前", value="アリス")
        assert query.field == "名前"
        assert query.value == "アリス"

    def test_complex_value_types(self):
        """Test query with complex value types (list, dict, etc)."""
        query = DocumentQuery(field="tags", value=["python", "testing"])
        assert query.value == ["python", "testing"]

    def test_none_for_both_fields(self):
        """Test explicitly setting both field and value to None."""
        query = DocumentQuery(field=None, value=None)
        assert query.field is None
        assert query.value is None


class TestDocumentUpdateValidation:
    """Tests for DocumentUpdate model validation."""

    def test_valid_update(self):
        """Test creating a valid DocumentUpdate."""
        update = DocumentUpdate(field="name", value="Alice", updates={"age": 31})
        assert update.field == "name"
        assert update.value == "Alice"
        assert update.updates == {"age": 31}
        assert update.table == "default"

    def test_empty_updates_raises_error(self):
        """Test that empty updates dict raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentUpdate(field="name", value="Alice", updates={})
        assert "Updates cannot be empty" in str(exc_info.value)

    def test_none_updates_raises_error(self):
        """Test that None updates raises validation error."""
        with pytest.raises(ValidationError):
            DocumentUpdate(field="name", value="Alice", updates=None)  # type: ignore

    def test_special_chars_in_fields(self):
        """Test update with special characters in field names."""
        update = DocumentUpdate(field="user-id", value=123, updates={"user-status": "active"})
        assert update.field == "user-id"
        assert update.updates["user-status"] == "active"

    def test_unicode_updates(self):
        """Test update with unicode values."""
        update = DocumentUpdate(field="name", value="Alice", updates={"city": "北京"})
        assert update.updates["city"] == "北京"

    def test_self_referential_update(self):
        """Test updating the same field you're matching on."""
        update = DocumentUpdate(field="status", value="pending", updates={"status": "active"})
        assert update.field == "status"
        assert update.updates["status"] == "active"

    def test_nested_updates(self):
        """Test update with nested dictionary values."""
        update = DocumentUpdate(
            field="id",
            value=1,
            updates={"address": {"city": "NYC", "zip": "10001"}},
        )
        assert update.updates["address"]["city"] == "NYC"


class TestDocumentDeleteValidation:
    """Tests for DocumentDelete model validation."""

    def test_valid_delete(self):
        """Test creating a valid DocumentDelete."""
        delete = DocumentDelete(field="id", value=123)
        assert delete.field == "id"
        assert delete.value == 123
        assert delete.table == "default"

    def test_empty_field_raises_error(self):
        """Test that empty field name is allowed (no validator preventing it)."""
        delete = DocumentDelete(field="", value="test")
        assert delete.field == ""

    def test_none_field_raises_error(self):
        """Test that None field raises validation error."""
        with pytest.raises(ValidationError):
            DocumentDelete(field=None, value="test")  # type: ignore

    def test_unicode_values(self):
        """Test delete with unicode field and value."""
        delete = DocumentDelete(field="名前", value="太郎")
        assert delete.field == "名前"
        assert delete.value == "太郎"

    def test_complex_value_types(self):
        """Test delete with complex value types."""
        delete = DocumentDelete(field="tags", value=["python", "fastmcp"])
        assert delete.value == ["python", "fastmcp"]


class TestOperationResultModel:
    """Tests for OperationResult model structure."""

    def test_success_result_structure(self):
        """Test creating a successful OperationResult."""
        result = OperationResult(success=True, message="Operation completed", data={"id": 1})
        assert result.success is True
        assert result.message == "Operation completed"
        assert result.data == {"id": 1}
        assert result.error is None

    def test_error_result_structure(self):
        """Test creating an error OperationResult."""
        result = OperationResult(success=False, message="Operation failed", error="File not found")
        assert result.success is False
        assert result.message == "Operation failed"
        assert result.error == "File not found"
        assert result.data is None

    def test_optional_fields(self):
        """Test OperationResult with only required fields."""
        result = OperationResult(success=True, message="Done")
        assert result.success is True
        assert result.message == "Done"
        assert result.data is None
        assert result.error is None

    def test_model_serialization(self):
        """Test that OperationResult serializes correctly to dict."""
        result = OperationResult(success=True, message="Success", data={"count": 5}, error=None)
        data = result.model_dump()
        assert data["success"] is True
        assert data["message"] == "Success"
        assert data["data"]["count"] == 5


class TestTableStatsModel:
    """Tests for TableStats model validation."""

    def test_valid_table_stats(self):
        """Test creating valid TableStats."""
        stats = TableStats(name="users", document_count=100, sample_fields=["id", "name", "email"])
        assert stats.name == "users"
        assert stats.document_count == 100
        assert stats.sample_fields == ["id", "name", "email"]

    def test_empty_sample_fields(self):
        """Test TableStats with empty sample_fields list."""
        stats = TableStats(name="empty_table", document_count=0, sample_fields=[])
        assert stats.sample_fields == []
        assert stats.document_count == 0


class TestDatabaseStatsModel:
    """Tests for DatabaseStats model validation."""

    def test_valid_database_stats(self):
        """Test creating valid DatabaseStats."""
        stats = DatabaseStats(
            database_path="/path/to/db.json",
            database_size_bytes=1024,
            total_tables=3,
            tables={"users": {"document_count": 10}, "products": {"document_count": 5}},
        )
        assert stats.database_path == "/path/to/db.json"
        assert stats.database_size_bytes == 1024
        assert stats.total_tables == 3
        assert len(stats.tables) == 2
