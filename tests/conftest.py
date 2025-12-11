"""Shared pytest fixtures and configuration for all tests."""

import os
import tempfile

import pytest


@pytest.fixture
def temp_readonly_file():
    """Create a temporary read-only file with valid JSON."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        f.write('{"test": "data"}')
        path = f.name
    os.chmod(path, 0o444)  # Read-only
    yield path
    os.chmod(path, 0o644)  # Restore permissions for cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temp_readonly_dir():
    """Create a temporary read-only directory."""
    tmpdir = tempfile.mkdtemp()
    os.chmod(tmpdir, 0o555)  # Read-only
    yield tmpdir
    os.chmod(tmpdir, 0o755)  # Restore permissions for cleanup
    if os.path.exists(tmpdir):
        os.rmdir(tmpdir)


@pytest.fixture
def corrupted_json_file():
    """Create a file with corrupted JSON (missing closing brace)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        f.write('{"incomplete": "json"')  # Missing closing brace
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def truncated_json_file():
    """Create a truncated JSON file (cut off mid-write)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        f.write('{"data": "test", "more":')  # Truncated mid-write
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def empty_json_file():
    """Create an empty JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        # Write nothing
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def binary_file():
    """Create a binary file (not JSON)."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".json") as f:
        f.write(b"\x00\x01\x02\x03\x04\x05")  # Binary data
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def large_document():
    """Generate a very large document (1MB+)."""
    return {f"field_{i}": "x" * 1000 for i in range(1000)}


@pytest.fixture
def deeply_nested_dict():
    """Generate deeply nested dictionary (50 levels)."""
    result = {"value": "deepest"}
    for i in range(50):
        result = {f"level_{i}": result}
    return result


@pytest.fixture
def unicode_test_data():
    """Unicode test data with various scripts and emoji."""
    return {
        "emoji": "🔥🎉👍😀",
        "chinese": "你好世界",
        "arabic": "مرحبا بالعالم",
        "japanese": "こんにちは世界",
        "mixed": "Hello 世界 🌍",
        "rtl": "שלום עולם",
        "emoji_key": {"🔥": "fire", "🎉": "party"},
    }


def create_large_dataset(db_manager, table: str, count: int = 10000):
    """Helper to create large datasets efficiently.

    Args:
        db_manager: TinyDBManager instance
        table: Table name
        count: Number of documents to create
    """
    table_obj = db_manager.get_table(table)
    docs = [{"id": i, "value": f"test_{i}"} for i in range(count)]
    table_obj.insert_multiple(docs)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "corruption: marks tests that create corrupted files")
    config.addinivalue_line("markers", "permissions: marks tests that modify file permissions")
