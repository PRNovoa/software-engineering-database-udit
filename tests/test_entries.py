from src.database import open_db
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
    lines = db_path.read_text(encoding="utf-8").splitlines()
    assert lines[-1] == "name:tombstoned"


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
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open(db_path, "w", encoding="utf-8") as db:
        create_entry("name", "pablo", db, cache)

    assert entry_exists("name", cache) is True
    assert entry_exists("missing", cache) is False
    
def test_update_entry(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open(db_path, "w", encoding="utf-8") as db:
        create_entry("name", "pablo", db, cache)

    assert update_entry("name", "gonzalo", db, cache) is True
    assert cache["name"] == "gonzalo"
    assert db_path.read_text(encoding="utf-8") == "name:pablo\nname:gonzalo\n"

    assert update_entry("missing", "x", db, cache) is False
    assert cache["name"] == "gonzalo"
    assert db_path.read_text(encoding="utf-8") == "name:pablo\nname:gonzalo\n"
    
def test_delete_entry(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open(db_path, "w", encoding="utf-8") as db:
        create_entry("name", "pablo", db, cache)

    assert delete_entry("name", db, cache) is True
    assert entry_exists("name", cache) is False
    assert read_entry("name", cache) is None
    lines = db_path.read_text(encoding="utf-8").splitlines()
    assert lines[-1] == "name:tombstoned"

    assert delete_entry("missing", db, cache) is False
    assert cache == {}
    assert db_path.read_text(encoding="utf-8") == "name:pablo\nname:tombstoned\n"    


  