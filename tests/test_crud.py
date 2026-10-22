from src.crud import create_entry, read_entry

def test_set(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open(db_path, "w", encoding="utf-8") as db:
        create_entry("name", "alice", db, cache)

    assert cache["name"] == "alice"
    contents = db_path.read_text(encoding="utf-8")
    assert "name" in contents and "alice" in contents

def test_get():
    cache = {"name": "alice"}
    assert read_entry("name", cache) == "alice"

# Set an existing key again and verify that its value is updated.
def test_set_existing_key(tmp_path):
    cache = {}
    with open(tmp_path / "test_database.txt", "w", encoding="utf-8") as db:
        create_entry("name", "alice", db, cache)
        create_entry("name", "bob", db, cache)
    assert read_entry("name", cache) == "bob"


# Verify that get() returns None for a missing key.
def test_get_missing_key():
    cache = {}
    assert read_entry("missing", cache) is None


# Verify that storing different keys preserves their individual values.
def test_different_keys(tmp_path):
    cache = {}
    with open(tmp_path / "test_database.txt", "w", encoding="utf-8") as db:
        create_entry("a", "1", db, cache)
        create_entry("b", "2", db, cache)
    assert read_entry("a", cache) == "1"
    assert read_entry("b", cache) == "2"