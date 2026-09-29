

# TODO: Move db handling to a separate module or class
def create_dictionary():
    global dictionary
    dictionary = {}
    with open("database.txt", "r", encoding="utf-8") as db:
        for line in db:
            k, v = line.strip().split(":", 1)
            dictionary[k] = v


# Dictionary should be initialized beforehand

def create_entry(key, value, db):
    db.write(f"{key}:{value}\n")
    dictionary[key] = value

def read_entry(key):
    return dictionary.get(key)

def update_entry(key, value, db): 
    # TODO 
    # Update the entry in the database and the dictionary
    # Should mark previous entry location with a tombstone
    return None

def delete_entry(key, db):
    # TODO
    # Mark the entry as deleted in the database and remove it from the dictionary
    # Should mark previous entry location with a tombstone
    return None

def delete_tombstones(db):
    # TODO
    # Remove all tombstone entries from the database
    return None