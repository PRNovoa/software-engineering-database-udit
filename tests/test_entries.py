from src.entries import create_entry, read_entry

def test_set(tmp_path):
    cache = {}
    db_path = tmp_path / "test_database.txt"
    with open(db_path, "w", encoding="utf-8") as db:
        create_entry("name", "pablo", db, cache)

    assert cache["name"] == "pablo"
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"

def test_get():
    cache = {"name": "pablo"}
    assert read_entry("name", cache) == "pablo"

# Set an existing key again and verify that its value is updated.
def test_set_existing_key(tmp_path):
    cache = {}
    with open(tmp_path / "test_database.txt", "w", encoding="utf-8") as db:
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
    with open(tmp_path / "test_database.txt", "w", encoding="utf-8") as db:
        create_entry("a", "1", db, cache)
        create_entry("b", "2", db, cache)
    assert read_entry("a", cache) == "1"
    assert read_entry("b", cache) == "2"