

# Dictionary should be initialized beforehand

def create_entry(key, value, db, cache):
    db.write(f"{key}:{value}\n")
    cache[key] = value

def read_entry(key, cache):
    return cache.get(key)

def update_entry(key, value, db, cache): 
    # TODO 
    # Update the entry in the database and the dictionary
    # Should mark previous entry location with a tombstone
    raise NotImplementedError("Update entry functionality is not implemented yet.")

def delete_entry(key, db, cache):
    # TODO
    # Mark the entry as deleted in the database and remove it from the dictionary
    # Should mark previous entry location with a tombstone
    raise NotImplementedError("Delete entry functionality is not implemented yet.")

def delete_tombstones(db):
    # TODO
    # Remove all tombstone entries from the database
    raise NotImplementedError("Delete tombstones functionality is not implemented yet.")