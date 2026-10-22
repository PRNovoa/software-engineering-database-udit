import os

def open_db(db_path):
    return open(db_path, "a+", encoding="utf-8")

def close_db(db):
    if db.closed:
        db.close()
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
