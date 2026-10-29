import os

TOMBSTONE_VALUE = "tombstoned"

def open_db(db_path: str | os.PathLike[str] | int, mode="a+"):
    """ Open the database file with the specified mode. """
    return open(db_path, mode, encoding="utf-8")

def create_cache(db) -> dict[str, str]:
    """ Create a cache from the database file. """
    cache = {}
    db.seek(0)
    for line in db:
        k, v = line.rstrip("\n").split(":", 1)
        cache[k] = v
    return cache

def start_db(db_path: str | os.PathLike[str] | int) -> tuple:
    """ Start the database by opening the file and creating a cache. Returns a tuple of (db, cache). """
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

def close_db(db) -> None:
    """ Close the database file. """
    if db.closed:
        return
    
    try:
        db.flush()
        os.fsync(db.fileno())
    finally: 
        db.close()

def compact_db(db) -> None:
    """ Compact the database file by removing tombstoned entries. """
    temp_cache = {}
    temp_path = db.name + ".tmp"

    db.seek(0)
    lines = db.readlines()
    
    if lines and not lines[-1].endswith("\n"):
        lines.pop()

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
