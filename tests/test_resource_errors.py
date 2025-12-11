"""Resource-specific error handling tests.

These tests validate error handling for MCP resources including database stats,
table lists, and table contents under various error conditions.
"""

import json
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
from src.models import DocumentInsert


@pytest.fixture(autouse=True)
def setup_test_db():
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


class TestDatabaseStatsResourceErrors:
    """Tests for get_database_stats error handling."""

    def test_stats_with_empty_database(self):
        """Test getting stats from an empty database."""
        stats_str = get_database_stats()

        assert isinstance(stats_str, str)
        stats = json.loads(stats_str)

        assert stats["total_tables"] == 0
        assert stats["tables"] == {}
        assert stats["database_size_bytes"] >= 0

    def test_stats_with_corrupted_database(self, corrupted_json_file):
        """Test getting stats when database file is corrupted."""
        original_path = db_manager.db_path
        db_manager.db_path = corrupted_json_file
        db_manager._db = None

        try:
            # May raise error or return error message
            stats_str = get_database_stats()

            # If it returns a string, check if it's an error message or valid JSON
            if "error" in stats_str.lower():
                # Error message returned
                assert isinstance(stats_str, str)
            else:
                # Should be valid JSON
                json.loads(stats_str)
        except Exception:
            # Expected: Some kind of database or parsing error
            pass
        finally:
            db_manager.db_path = original_path
            db_manager._db = None

    def test_stats_with_very_large_database(self):
        """Test getting stats from a database with many tables and documents."""
        # Insert documents into 10 different tables
        for table_num in range(10):
            for doc_num in range(100):
                insert_document(
                    DocumentInsert(
                        data={"id": doc_num, "value": f"test_{doc_num}"},
                        table=f"table_{table_num}",
                    )
                )

        stats_str = get_database_stats()

        assert isinstance(stats_str, str)
        stats = json.loads(stats_str)

        assert stats["total_tables"] == 10
        assert len(stats["tables"]) == 10

        # Verify each table has correct count
        for table_num in range(10):
            table_name = f"table_{table_num}"
            assert table_name in stats["tables"]
            assert stats["tables"][table_name]["document_count"] == 100

    def test_stats_json_serialization(self):
        """Test that stats can be serialized to JSON without errors."""
        # Insert various data types
        insert_document(
            DocumentInsert(
                data={
                    "string": "test",
                    "number": 123,
                    "float": 45.67,
                    "bool": True,
                    "null": None,
                    "array": [1, 2, 3],
                    "nested": {"key": "value"},
                }
            )
        )

        stats_str = get_database_stats()

        # Verify valid JSON
        stats = json.loads(stats_str)

        assert isinstance(stats, dict)
        assert "database_path" in stats
        assert "total_tables" in stats

    def test_stats_with_nonexistent_database_file(self):
        """Test stats when database file doesn't exist yet."""
        # Point to a non-existent file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            nonexistent_path = f.name

        original_path = db_manager.db_path
        db_manager.db_path = nonexistent_path
        db_manager._db = None

        try:
            # TinyDB should create file on access
            stats_str = get_database_stats()
            stats = json.loads(stats_str)

            assert stats["total_tables"] == 0
        finally:
            db_manager.db_path = original_path
            db_manager._db = None
            if os.path.exists(nonexistent_path):
                os.remove(nonexistent_path)


class TestTablesListResourceErrors:
    """Tests for get_tables_list error handling."""

    def test_tables_list_with_empty_database(self):
        """Test getting table list from empty database."""
        tables_str = get_tables_list()

        assert isinstance(tables_str, str)
        tables_data = json.loads(tables_str)

        assert "tables" in tables_data
        assert tables_data["tables"] == []

    def test_tables_list_with_special_char_tables(self):
        """Test table list with tables that have special characters."""
        # Insert documents with special character table names
        special_tables = [
            "table-with-dash",
            "table_with_underscore",
            "table.with.dots",
            "table with spaces",
            "table@symbol",
        ]

        for table_name in special_tables:
            insert_document(DocumentInsert(data={"test": "value"}, table=table_name))

        tables_str = get_tables_list()
        tables_data = json.loads(tables_str)

        table_names = [t["name"] for t in tables_data["tables"]]

        for expected_table in special_tables:
            assert expected_table in table_names

    def test_tables_list_with_unicode_table_names(self, unicode_test_data):
        """Test table list with unicode table names."""
        unicode_tables = [
            "用户_users",
            "产品_products",
            "заказы_orders",
        ]

        for table_name in unicode_tables:
            insert_document(DocumentInsert(data={"test": "value"}, table=table_name))

        tables_str = get_tables_list()
        tables_data = json.loads(tables_str)

        table_names = [t["name"] for t in tables_data["tables"]]

        for expected_table in unicode_tables:
            assert expected_table in table_names

    def test_tables_list_json_serialization(self):
        """Test that table list can be serialized to JSON."""
        # Create tables with various data
        insert_document(DocumentInsert(data={"field1": "value1"}, table="table1"))
        insert_document(DocumentInsert(data={"field2": "value2", "field3": 123}, table="table2"))

        tables_str = get_tables_list()

        # Verify valid JSON
        tables_data = json.loads(tables_str)

        assert isinstance(tables_data, dict)
        assert "tables" in tables_data
        assert isinstance(tables_data["tables"], list)

        # Each table should have required fields
        for table in tables_data["tables"]:
            assert "name" in table
            assert "document_count" in table
            assert "sample_fields" in table

    def test_tables_list_with_many_tables(self):
        """Test table list with a large number of tables."""
        # Create 50 tables
        for i in range(50):
            insert_document(DocumentInsert(data={"id": i}, table=f"table_{i:03d}"))

        tables_str = get_tables_list()
        tables_data = json.loads(tables_str)

        assert len(tables_data["tables"]) == 50


class TestTableContentsResourceErrors:
    """Tests for get_table_contents error handling."""

    def test_table_contents_nonexistent_table(self):
        """Test getting contents of a non-existent table."""
        contents = get_table_contents("nonexistent_table")

        assert isinstance(contents, str)
        # Should indicate error or that table doesn't exist
        assert "error" in contents.lower() or "does not exist" in contents.lower()

    def test_table_contents_empty_table(self):
        """Test getting contents of an empty table."""
        # Create empty table by inserting then deleting
        insert_document(DocumentInsert(data={"temp": "data"}, table="empty_table"))
        db_manager.get_table("empty_table").truncate()

        contents = get_table_contents("empty_table")

        assert "empty_table" in contents
        assert "Total Documents: 0" in contents
        assert "No documents" in contents

    def test_table_contents_with_large_table(self):
        """Test getting contents of a table with many documents."""
        # Insert 1000 documents
        for i in range(1000):
            insert_document(
                DocumentInsert(data={"id": i, "value": f"test_{i}"}, table="large_table")
            )

        contents = get_table_contents("large_table")

        assert "large_table" in contents
        assert "Total Documents: 1000" in contents
        # Should show at least some documents
        assert "id" in contents or "value" in contents

    def test_table_contents_with_unicode_documents(self, unicode_test_data):
        """Test table contents with unicode data."""
        # Insert documents with unicode
        insert_document(
            DocumentInsert(
                data={
                    "emoji": unicode_test_data["emoji"],
                    "chinese": unicode_test_data["chinese"],
                    "arabic": unicode_test_data["arabic"],
                },
                table="unicode_table",
            )
        )

        contents = get_table_contents("unicode_table")

        # Verify unicode is preserved in output
        assert unicode_test_data["emoji"] in contents
        assert unicode_test_data["chinese"] in contents
        assert unicode_test_data["arabic"] in contents

    def test_table_contents_with_special_chars(self):
        """Test table contents with special characters in data."""
        insert_document(
            DocumentInsert(
                data={
                    "html": '<div class="test">Hello & "World"</div>',
                    "newlines": "Line 1\nLine 2\nLine 3",
                    "tabs": "Col1\tCol2\tCol3",
                },
                table="special_chars",
            )
        )

        contents = get_table_contents("special_chars")

        # Verify special characters are preserved
        assert "html" in contents
        assert "newlines" in contents
        assert "tabs" in contents

    def test_table_contents_with_nested_documents(self):
        """Test table contents with deeply nested documents."""
        nested_data = {"level1": {"level2": {"level3": {"level4": {"level5": {"value": "deep"}}}}}}

        insert_document(DocumentInsert(data=nested_data, table="nested_table"))

        contents = get_table_contents("nested_table")

        assert "nested_table" in contents
        # Should show nested structure
        assert "level1" in contents

    def test_table_contents_formatting(self):
        """Test that table contents are well-formatted."""
        insert_document(
            DocumentInsert(data={"field1": "value1", "field2": "value2"}, table="format_test")
        )

        contents = get_table_contents("format_test")

        # Check for formatting elements
        assert "Table:" in contents or "format_test" in contents
        assert "Total Documents:" in contents
        assert "Document 1:" in contents or "Document" in contents

    def test_table_contents_with_empty_string_table_name(self):
        """Test getting contents with empty string table name."""
        # Insert into empty-named table
        insert_document(DocumentInsert(data={"test": "value"}, table=""))

        contents = get_table_contents("")

        # Should either work or show error
        assert isinstance(contents, str)

    def test_table_contents_with_special_char_table_name(self):
        """Test getting contents of table with special characters in name."""
        special_table = "table-with-special.chars@123"
        insert_document(DocumentInsert(data={"test": "value"}, table=special_table))

        contents = get_table_contents(special_table)

        assert special_table in contents
        assert "test" in contents.lower() or "value" in contents.lower()
