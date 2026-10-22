import os

def open_db(db_path):
    return open(db_path, "a+", encoding="utf-8")

def create_cache(db):
    cache = {}
    db.seek(0)
    for line in db:
        k, v = line.rstrip("\n").split(":", 1)
        cache[k] = v
    return cache

def start_db(db_path):
    with open_db(db_path) as db:
        compact_db(db)

    db = open_db(db_path)
    cache = create_cache(db)
    return db, cache

def compact_db(db):
    temp_cache = {}
    temp_path = db.name + ".tmp"

    db.seek(0)
    lines = db.readlines()

    with open(temp_path, "w", encoding="utf-8") as db_temp:

        for line in reversed(lines):
            key, value = line.rstrip("\n").split(":", 1,)
            if key not in temp_cache:
                temp_cache[key] = value

        for key, value in reversed(temp_cache.items()):
            if value != "tombstoned":
                db_temp.write(f"{key}:{value}\n")

        db_temp.flush()
        os.fsync(db_temp.fileno())
    os.replace(temp_path, db.name)

