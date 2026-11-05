import pytest

from src.database import open_db
from src.exceptions import DatabaseError, InvalidEntryError
from src.entries import (
    create_entry,
    read_entry,
    update_entry,
    delete_entry,
    entry_exists,
)


def test_set(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)

    assert cache["name"] == "pablo"
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"

def test_get():
    cache = {"name": "pablo"}
    assert read_entry("name", cache) == "pablo"

# Set an existing key again and verify that its value is updated.
def test_set_existing_key(tmp_path):
    cache = {}
    with open_db(tmp_path / "test_database.txt") as db:
        create_entry("name", "pablo", db, cache)
        create_entry("name", "gonzalo", db, cache)
    assert read_entry("name", cache) == "gonzalo"


# Verify that get() returns None for a missing key.
def test_get_missing_key():
    cache = {}
    assert read_entry("missing", cache) is None


# Verify that storing different keys preserves their individual values.
def test_different_keys(tmp_path):
    cache = {}
    with open_db(tmp_path / "test_database.txt") as db:
        create_entry("a", "1", db, cache)
        create_entry("b", "2", db, cache)
    assert read_entry("a", cache) == "1"
    assert read_entry("b", cache) == "2"


# Update an existing key: returns True.
def test_update_existing_key(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert update_entry("name", "gonzalo", db, cache) is True

    assert cache["name"] == "gonzalo"
    assert db_path.read_text(encoding="utf-8") == "name:pablo\nname:gonzalo\n"


# Update a missing key: returns False.
def test_update_missing_key(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert update_entry("missing", "x", db, cache) is False

    assert cache == {"name": "pablo"}
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


# Delete an existing key: returns True.
def test_delete_existing_key(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert delete_entry("name", db, cache) is True

    assert entry_exists("name", cache) is False
    assert read_entry("name", cache) is None
    assert cache == {}
    assert db_path.read_text(encoding="utf-8") == "name:pablo\nname:tombstoned\n"
    

# Delete a missing key: returns False.
def test_delete_missing_key(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert delete_entry("missing", db, cache) is False

    assert cache == {"name": "pablo"}
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


# Delete the same key twice: second call returns False, only one tombstone written.
def test_delete_twice(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open_db(db_path) as db:
        create_entry("name", "pablo", db, cache)
        assert delete_entry("name", db, cache) is True
        assert delete_entry("name", db, cache) is False

    assert db_path.read_text(encoding="utf-8") == "name:pablo\nname:tombstoned\n"


def test_entry_exists(tmp_path):        
    cache = {"name": "pablo"}    

    assert entry_exists("name", cache) is True
    assert entry_exists("missing", cache) is False

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

# Invalid entries raise InvalidEntryError without touching the file or the cache.
@pytest.mark.parametrize("key, value", INVALID_ENTRIES)
def test_create_invalid_entry_raises_without_side_effects(tmp_path, key, value):
    cache = {"name": "pablo"}
    db_path = tmp_path / "test_database.txt"
    db_path.write_text("name:pablo\n", encoding="utf-8")

    with open_db(db_path) as db:
        with pytest.raises(InvalidEntryError):
            create_entry(key, value, db, cache)

    assert cache == {"name": "pablo"}
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


# InvalidEntryError can still be caught as ValueError and as DatabaseError.
@pytest.mark.parametrize("base_exception", [ValueError, DatabaseError])
def test_invalid_entry_error_is_caught_by_base_classes(tmp_path, base_exception):
    with open_db(tmp_path / "test_database.txt") as db:
        with pytest.raises(base_exception) as exc_info:
            create_entry("a:b", "value", db, {})

    assert isinstance(exc_info.value, InvalidEntryError)
