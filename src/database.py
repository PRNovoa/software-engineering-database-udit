import os

TOMBSTONE_VALUE = "tombstoned"

def open_db(db_path, mode="a+"):
    return open(db_path, mode, encoding="utf-8")

def create_cache(db):
    cache = {}
    db.seek(0)
    for line in db:
        k, v = line.rstrip("\n").split(":", 1)
        cache[k] = v
    return cache

def start_db(db_path):
    db = open_db(db_path)
    try:
        compact_db(db)
    finally:
        db.close()

    db = open_db(db_path)
    try:
        cache = create_cache(db)
    except BaseException: 
        db.close()
        raise

    return db, cache

def close_db(db):
    if db.closed:
        return
    
    try:
        db.flush()
        os.fsync(db.fileno())
    finally: 
        db.close()

def compact_db(db):
    temp_cache = {}
    temp_path = db.name + ".tmp"

    db.seek(0)
    lines = db.readlines()

    with open_db(temp_path, "w") as db_temp:

        for line in reversed(lines):
            key, value = line.rstrip("\n").split(":", 1,)
            if key not in temp_cache:
                temp_cache[key] = value

        for key, value in reversed(temp_cache.items()):
            if value != TOMBSTONE_VALUE:
                db_temp.write(f"{key}:{value}\n")

        db_temp.flush()
        os.fsync(db_temp.fileno())
    os.replace(temp_path, db.name)
