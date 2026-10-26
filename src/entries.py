# Dictionary should be initialized beforehand

from src.database import TOMBSTONE_VALUE

def validate_entry(key, value, allow_tombstone=False):
    
    if not isinstance(key, str) or not isinstance(value, str):
        raise ValueError("Key and value must be strings.")

    if not key:
        raise ValueError("Key cannot be empty.")
  
    try: 
        key.encode("utf-8")
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("Key and value must be valid UTF-8 strings.")

    if ":" in key:
        raise ValueError("Key cannot contain ':' character.")
    if "\n" in key or "\r" in key or "\n" in value or "\r" in value:
        raise ValueError("Key and value cannot contain newline characters.")
    if not allow_tombstone and value == TOMBSTONE_VALUE:
        raise ValueError("Tombstoned values are not allowed.")

def create_entry(key, value, db, cache, allow_tombstone=False):
    validate_entry(key, value, allow_tombstone)
    db.write(f"{key}:{value}\n")
    cache[key] = value

def read_entry(key, cache):
    return cache.get(key)

def update_entry(key, value, db, cache): 
    if entry_exists(key, cache):
        create_entry(key, value, db, cache)
        return True
    return False

def entry_exists(key, cache):
    return key in cache

def delete_entry(key, db, cache):
    if entry_exists(key, cache):
        create_entry(key, TOMBSTONE_VALUE, db, cache, allow_tombstone=True)
        del cache[key]
        return True
    return False