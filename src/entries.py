# TODO: Move db handling to a separate module or class
def create_cache():
    cache = {}
    with open("database.txt", "r", encoding="utf-8") as db:
        for line in db:
            k, v = line.strip().split(":", 1)
            cache[k] = v


# Dictionary should be initialized beforehand

def create_entry(key, value, db, cache):
    db.write(f"{key}:{value}\n")
    cache[key] = value

def read_entry(key, cache):
    return cache.get(key)

def update_entry(key, value, db, cache): 
    if key not in cache:
        return False
        
    create_entry(key, value, db, cache)
    return True

def entry_exists(key, cache):
    return key in cache

def delete_entry(key, db, cache):
    if entry_exists(key, cache):
        create_entry(key, "tombstoned", db, cache)
        del cache[key]
        return True
    return False

def delete_tombstones(db):
    # TODO
    # Remove all tombstone entries from the database
    raise NotImplementedError("Delete tombstones functionality is not implemented yet.")