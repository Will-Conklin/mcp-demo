"""Tests for TinyDBManager class."""

import os
import tempfile

import pytest

from src.mcp_tinydb_server import TinyDBManager


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        db_path = f.name

    manager = TinyDBManager(db_path)
    yield manager

    # Cleanup
    manager.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_manager_initialization(temp_db):
    """Test that TinyDBManager initializes correctly."""
    assert temp_db.db_path is not None
    assert temp_db._db is None  # Lazy initialization


def test_lazy_database_creation(temp_db):
    """Test that database is created lazily on first access."""
    assert temp_db._db is None
    db = temp_db.db
    assert db is not None
    assert temp_db._db is not None


def test_get_table(temp_db):
    """Test getting a table from the database."""
    table = temp_db.get_table("test_table")
    assert table is not None
    assert table.name == "test_table"


def test_get_all_tables_empty(temp_db):
    """Test getting all tables when database is empty."""
    tables = temp_db.get_all_tables()
    assert isinstance(tables, list)
    assert len(tables) == 0


def test_get_all_tables_with_data(temp_db):
    """Test getting all tables after creating some."""
    # TinyDB only registers tables after inserting data
    temp_db.get_table("table1").insert({"data": "test1"})
    temp_db.get_table("table2").insert({"data": "test2"})
    temp_db.get_table("table3").insert({"data": "test3"})

    tables = temp_db.get_all_tables()
    assert len(tables) == 3
    assert "table1" in tables
    assert "table2" in tables
    assert "table3" in tables


def test_get_stats_empty_db(temp_db):
    """Test getting stats from an empty database."""
    stats = temp_db.get_stats()

    assert "database_path" in stats
    assert "total_tables" in stats
    assert "database_size_bytes" in stats
    assert "tables" in stats

    assert stats["total_tables"] == 0
    assert isinstance(stats["tables"], dict)
    assert len(stats["tables"]) == 0


def test_get_stats_with_data(temp_db):
    """Test getting stats from a database with data."""
    # Add some test data
    table1 = temp_db.get_table("users")
    table1.insert({"name": "Alice", "age": 30})
    table1.insert({"name": "Bob", "age": 25})

    table2 = temp_db.get_table("products")
    table2.insert({"name": "Widget", "price": 9.99})

    stats = temp_db.get_stats()

    assert stats["total_tables"] == 2
    assert "users" in stats["tables"]
    assert "products" in stats["tables"]
    assert stats["tables"]["users"]["document_count"] == 2
    assert stats["tables"]["products"]["document_count"] == 1
    assert stats["database_size_bytes"] > 0


def test_close_database(temp_db):
    """Test closing the database connection."""
    # Access db to ensure it's initialized
    _ = temp_db.db
    assert temp_db._db is not None

    # Close it
    temp_db.close()
    assert temp_db._db is None


def test_database_file_creation():
    """Test that database file is created on disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.json")

        manager = TinyDBManager(db_path)

        # Database file shouldn't exist yet (lazy init)
        assert not os.path.exists(db_path)

        # Access the db
        _ = manager.db

        # Now file should exist
        assert os.path.exists(db_path)

        manager.close()
