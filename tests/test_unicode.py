"""Unicode and special character handling tests.

These tests validate unicode support, emoji, special characters, and edge cases
with field names to ensure robustness with international data.
"""

import os
import tempfile

import pytest

from src.mcp_tinydb_server import (
    db_manager,
    delete_documents,
    insert_document,
    query_documents,
    update_documents,
)
from src.models import DocumentDelete, DocumentInsert, DocumentQuery, DocumentUpdate


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


class TestUnicodeSupport:
    """Tests for unicode character support across different scripts."""

    def test_insert_emoji_in_data(self, unicode_test_data):
        """Test inserting documents with emoji characters."""
        result = insert_document(DocumentInsert(data={"emoji": unicode_test_data["emoji"]}))

        assert result.success is True
        assert result.data is not None

        # Verify emoji persisted
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["emoji"] == unicode_test_data["emoji"]

    def test_insert_chinese_characters(self, unicode_test_data):
        """Test inserting documents with Chinese characters."""
        result = insert_document(DocumentInsert(data={"text": unicode_test_data["chinese"]}))

        assert result.success is True

        # Verify Chinese text persisted
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["text"] == unicode_test_data["chinese"]

    def test_insert_arabic_text(self, unicode_test_data):
        """Test inserting documents with Arabic (RTL) text."""
        result = insert_document(DocumentInsert(data={"greeting": unicode_test_data["arabic"]}))

        assert result.success is True

        # Verify Arabic text persisted
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["greeting"] == unicode_test_data["arabic"]

    def test_insert_mixed_scripts(self, unicode_test_data):
        """Test inserting documents with mixed scripts (Latin, CJK, emoji)."""
        result = insert_document(DocumentInsert(data={"mixed": unicode_test_data["mixed"]}))

        assert result.success is True

        # Verify mixed text persisted
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["mixed"] == unicode_test_data["mixed"]

    def test_emoji_as_field_name(self):
        """Test using emoji as field name."""
        result = insert_document(DocumentInsert(data={"🔥": "fire", "🎉": "party"}))

        assert result.success is True

        # Verify emoji field names work
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["🔥"] == "fire"
        assert query_result.data["documents"][0]["🎉"] == "party"

    def test_unicode_table_name(self):
        """Test using unicode characters in table names."""
        result = insert_document(DocumentInsert(data={"name": "test"}, table="用户_users"))

        assert result.success is True
        assert result.data is not None
        assert result.data["table"] == "用户_users"

    def test_query_with_unicode_value(self, unicode_test_data):
        """Test querying documents with unicode values."""
        # Insert document with unicode
        insert_document(DocumentInsert(data={"name": unicode_test_data["chinese"]}))

        # Query with unicode value
        result = query_documents(DocumentQuery(field="name", value=unicode_test_data["chinese"]))

        assert result.success is True
        assert result.data is not None
        assert result.data["count"] == 1
        assert result.data["documents"][0]["name"] == unicode_test_data["chinese"]

    def test_update_with_unicode(self, unicode_test_data):
        """Test updating documents with unicode values."""
        # Insert document
        insert_document(DocumentInsert(data={"name": "test"}))

        # Update with unicode
        result = update_documents(
            DocumentUpdate(
                field="name", value="test", updates={"name": unicode_test_data["japanese"]}
            )
        )

        assert result.success is True
        assert result.data is not None
        assert result.data["updated_count"] >= 1

        # Verify update
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["name"] == unicode_test_data["japanese"]

    def test_rtl_text_handling(self, unicode_test_data):
        """Test right-to-left text (Hebrew, Arabic) handling."""
        result = insert_document(
            DocumentInsert(
                data={
                    "hebrew": unicode_test_data["rtl"],
                    "arabic": unicode_test_data["arabic"],
                }
            )
        )

        assert result.success is True

        # Verify RTL text persisted correctly
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        doc = query_result.data["documents"][0]
        assert doc["hebrew"] == unicode_test_data["rtl"]
        assert doc["arabic"] == unicode_test_data["arabic"]

    def test_unicode_normalization(self):
        """Test that unicode normalization doesn't affect storage."""
        # Using composed vs decomposed unicode (é can be one char or e + accent)
        composed = "café"  # Single character é
        decomposed = "cafe\u0301"  # e + combining acute accent

        insert_document(DocumentInsert(data={"composed": composed}))
        insert_document(DocumentInsert(data={"decomposed": decomposed}))

        result = query_documents(DocumentQuery())
        assert result.data is not None
        assert result.data["count"] == 2

        # Both forms should be stored as-is
        docs = result.data["documents"]
        assert docs[0]["composed"] == composed
        assert docs[1]["decomposed"] == decomposed


class TestSpecialCharacters:
    """Tests for special characters and control characters."""

    def test_newlines_in_values(self):
        """Test documents with newline characters in values."""
        multiline_text = "Line 1\nLine 2\nLine 3"
        result = insert_document(DocumentInsert(data={"text": multiline_text}))

        assert result.success is True

        # Verify newlines preserved
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["text"] == multiline_text

    def test_tabs_in_values(self):
        """Test documents with tab characters in values."""
        tabbed_text = "Column1\tColumn2\tColumn3"
        result = insert_document(DocumentInsert(data={"text": tabbed_text}))

        assert result.success is True

        # Verify tabs preserved
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["text"] == tabbed_text

    def test_html_special_chars(self):
        """Test HTML/XML special characters."""
        html_text = '<div class="test">Hello & "World"</div>'
        result = insert_document(DocumentInsert(data={"html": html_text}))

        assert result.success is True

        # Verify HTML chars preserved (not escaped)
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["html"] == html_text

    def test_quotes_in_values(self):
        """Test single and double quotes in values."""
        text_with_quotes = "He said \"Hello\" and she said 'Hi'"
        result = insert_document(DocumentInsert(data={"text": text_with_quotes}))

        assert result.success is True

        # Verify quotes preserved
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["text"] == text_with_quotes

    def test_backslashes_in_values(self):
        """Test backslashes in values (Windows paths, etc)."""
        windows_path = r"C:\Users\test\Documents\file.txt"
        result = insert_document(DocumentInsert(data={"path": windows_path}))

        assert result.success is True

        # Verify backslashes preserved
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["path"] == windows_path

    def test_zero_width_characters(self):
        """Test zero-width unicode characters."""
        # Zero-width space, zero-width joiner, zero-width non-joiner
        text_with_zwc = "Hello\u200bWorld\u200c\u200d"
        result = insert_document(DocumentInsert(data={"text": text_with_zwc}))

        assert result.success is True

        # Verify zero-width chars preserved
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0]["text"] == text_with_zwc


class TestFieldNameEdgeCases:
    """Tests for edge cases with field names."""

    def test_field_names_with_dots(self):
        """Test field names containing dots."""
        result = insert_document(
            DocumentInsert(data={"user.name": "Alice", "config.setting": "value"})
        )

        assert result.success is True

        # Verify dotted field names work
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        doc = query_result.data["documents"][0]
        assert doc["user.name"] == "Alice"
        assert doc["config.setting"] == "value"

    def test_field_names_with_spaces(self):
        """Test field names containing spaces."""
        result = insert_document(DocumentInsert(data={"first name": "Alice", "last name": "Smith"}))

        assert result.success is True

        # Verify spaced field names work
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        doc = query_result.data["documents"][0]
        assert doc["first name"] == "Alice"
        assert doc["last name"] == "Smith"

    def test_field_names_with_special_chars(self):
        """Test field names with various special characters."""
        result = insert_document(
            DocumentInsert(
                data={
                    "key-with-dash": "value1",
                    "key_with_underscore": "value2",
                    "key@symbol": "value3",
                    "key#hash": "value4",
                }
            )
        )

        assert result.success is True

        # Verify all special char field names work
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        doc = query_result.data["documents"][0]
        assert doc["key-with-dash"] == "value1"
        assert doc["key_with_underscore"] == "value2"
        assert doc["key@symbol"] == "value3"
        assert doc["key#hash"] == "value4"

    def test_very_long_field_names(self):
        """Test field names with extreme length (1000+ chars)."""
        long_key = "x" * 1000
        result = insert_document(DocumentInsert(data={long_key: "value"}))

        assert result.success is True

        # Verify long field name works
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["documents"][0][long_key] == "value"

    def test_numeric_field_names(self):
        """Test purely numeric field names (as strings)."""
        result = insert_document(DocumentInsert(data={"123": "value1", "456.789": "value2"}))

        assert result.success is True

        # Verify numeric field names work
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        doc = query_result.data["documents"][0]
        assert doc["123"] == "value1"
        assert doc["456.789"] == "value2"

    def test_delete_with_unicode_field(self, unicode_test_data):
        """Test deleting documents with unicode field names/values."""
        # Insert document with unicode
        insert_document(DocumentInsert(data={"名前": unicode_test_data["japanese"]}))

        # Delete using unicode field
        result = delete_documents(DocumentDelete(field="名前", value=unicode_test_data["japanese"]))

        assert result.success is True
        assert result.data is not None
        assert result.data["deleted_count"] >= 1

        # Verify deletion
        query_result = query_documents(DocumentQuery())
        assert query_result.data is not None
        assert query_result.data["count"] == 0
