from crud import create_entry, read_entry

#Set a key-value pair and verify that get() returns the stored value.
def test_set_and_get():
    cache = {}
    with open("test_database.txt", "w", encoding="utf-8") as db:
        create_entry("name", "alice", db, cache)
    if read_entry("name", cache) == "alice":
        print("OK    test_set_and_get")
    else:
        print("FALLO test_set_and_get")

#Set an existing key again and verify that its value is updated.
def test_set_existing_key():
    cache = {}
    with open("test_database.txt", "w", encoding="utf-8") as db:
        create_entry("name", "alice", db, cache)
        create_entry("name", "bob", db, cache)
    if read_entry("name", cache) == "bob":
        print("OK    test_set_existing_key")
    else:
        print("FAIL test_set_existing_key")

#Verify that get() returns None for a missing key.
def test_get_missing_key():
    cache = {}
    if read_entry("missing", cache) is None:
        print("OK    test_get_missing_key")
    else:
        print("FAIL test_get_missing_key")

#Verify that storing different keys preserves their individual values.
def test_different_keys():
    cache = {}
    with open("test_database.txt", "w", encoding="utf-8") as db:
        create_entry("a", "1", db, cache)
        create_entry("b", "2", db, cache)
    if read_entry("a", cache) == "1" and read_entry("b", cache) == "2":
        print("OK    test_different_keys")
    else:
        print("FAIL test_different_keys")




test_set_and_get()
test_set_existing_key()
test_get_missing_key()
test_different_keys()