import os
from multiprocessing import Process
from unittest.mock import patch

import pytest

from src.database import compact_db, open_db, start_db
from src.exceptions import DatabaseError, InvalidEntryError
from src.database import open_db
from src.entries import (
    create_entry,
    delete_entry,
    entry_exists,
    read_entry,
    update_entry,
)


def test_set(tmp_path):
    """Create a new entry: it is stored in the cache and appended to the file."""
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)

    assert cache["name"] == "pablo"
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"

def test_get():
    """Read an existing key: returns its value from the cache."""
    cache = {"name": "pablo"}
    assert read_entry("name", cache) == "pablo"

def test_set_existing_key(tmp_path):
    """Set an existing key again and verify that its value is updated."""
    cache = {}
    with open_db(tmp_path / "test_database.txt") as db:
        create_entry("name", "pablo", db, cache)
        create_entry("name", "gonzalo", db, cache)
    assert read_entry("name", cache) == "gonzalo"


def test_get_missing_key():
    """Verify that get() returns None for a missing key."""
    cache = {}
    assert read_entry("missing", cache) is None


def test_different_keys(tmp_path):
    """Verify that storing different keys preserves their individual values."""
    cache = {}
    with open_db(tmp_path / "test_database.txt") as db:
        create_entry("a", "1", db, cache)
        create_entry("b", "2", db, cache)
    assert read_entry("a", cache) == "1"
    assert read_entry("b", cache) == "2"


def test_update_existing_key(tmp_path):
    """Update an existing key: returns True."""
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert update_entry("name", "gonzalo", db, cache) is True

    assert cache["name"] == "gonzalo"
    assert db_path.read_text(encoding="utf-8") == "name:pablo\nname:gonzalo\n"

def  test_update_write_fails_keeps_cache():
    """If writing the update fails, the error reaches the caller and the cache is unchanged."""
    cache = {"name": "pablo", "city": "Madrid"}

    class FailingDB:
        def write(self, data):
            raise OSError("Simulated write failure")

    with pytest.raises(OSError):
        update_entry("name", "gonzalo", FailingDB(), cache)

    assert cache == {"name": "pablo", "city": "Madrid"}

def test_update_missing_key(tmp_path):
    """Update a missing key: returns False."""
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert update_entry("missing", "x", db, cache) is False

    assert cache == {"name": "pablo"}
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


def test_delete_existing_key(tmp_path):
    """Delete an existing key: returns True."""
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert delete_entry("name", db, cache) is True

    assert entry_exists("name", cache) is False
    assert read_entry("name", cache) is None
    assert cache == {}
    assert db_path.read_text(encoding="utf-8") == "name:pablo\nname:tombstoned\n"
    

def test_delete_missing_key(tmp_path):
    """Delete a missing key: returns False."""
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert delete_entry("missing", db, cache) is False

    assert cache == {"name": "pablo"}
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


def test_delete_twice(tmp_path):
    """Delete the same key twice: second call returns False, only one tombstone written."""
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert delete_entry("name", db, cache) is True
        assert delete_entry("name", db, cache) is False

    assert db_path.read_text(encoding="utf-8") == "name:pablo\nname:tombstoned\n"


def test_entry_exists(tmp_path):
    """entry_exists() returns True for a key in the cache and False for a missing one."""
    cache = {"name": "pablo"}    

    assert entry_exists("name", cache) is True
    assert entry_exists("missing", cache) is False

def write_and_exit(db_path):
    """Write an entry to the database and exit the process."""
    db, cache = start_db(db_path)
    create_entry("name", "pablo", db, cache)
    os._exit(0)

def test_new_entry_survives_sudden_exit(tmp_path):
    """Test that a new entry survives a sudden exit of the process."""
    db_path = tmp_path / "test_database.txt"

    process = Process(target=write_and_exit, args=(db_path,))
    process.start()
    process.join()

    assert process.exitcode == 0
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"

INVALID_ENTRIES = [
    pytest.param(1, "value", id="non-string key"),
    pytest.param("key", None, id="non-string value"),
    pytest.param("", "value", id="empty key"),
    pytest.param("\ud800", "value", id="non-utf8 key"),
    pytest.param("key", "\ud800", id="non-utf8 value"),
    pytest.param("a:b", "value", id="colon in key"),
    pytest.param("a\nb", "value", id="newline in key"),
    pytest.param("a\rb", "value", id="carriage return in key"),
    pytest.param("key", "a\nb", id="newline in value"),
    pytest.param("key", "a\rb", id="carriage return in value"),
    pytest.param("key", "tombstoned", id="tombstone value"),
]

@pytest.mark.parametrize("key, value", INVALID_ENTRIES)
def test_create_invalid_entry_raises_without_side_effects(tmp_path, key, value):
    """Invalid entries raise InvalidEntryError without touching the file or the cache."""
    cache = {"name": "pablo"}
    db_path = tmp_path / "test_database.txt"
    db_path.write_text("name:pablo\n", encoding="utf-8")

    with open_db(db_path) as db:
        with pytest.raises(InvalidEntryError):
            create_entry(key, value, db, cache)

    assert cache == {"name": "pablo"}
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


@pytest.mark.parametrize("base_exception", [ValueError, DatabaseError])
def test_invalid_entry_error_is_caught_by_base_classes(tmp_path, base_exception):
    """InvalidEntryError can still be caught as ValueError and as DatabaseError."""
    with open_db(tmp_path / "test_database.txt") as db:
        with pytest.raises(base_exception) as exc_info:
            create_entry("a:b", "value", db, {})

    assert isinstance(exc_info.value, InvalidEntryError)
