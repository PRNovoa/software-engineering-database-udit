import os

def compact_db(db_path):
    temp_cache = {}
    temp_path = db_path + ".tmp"

    with open(db_path, "r", encoding="utf-8") as db:
        lines = db.readlines()

    with open(temp_path, "w", encoding="utf-8") as db_temp:

        for line in reversed(lines):
            key, value = line.rstrip("\n").split(":", 1,)
            if key not in temp_cache:
                temp_cache[key] = value

        for key, value in reversed(temp_cache.items()):
            if value != "toombstoned":
                db_temp.write(f"{key}:{value}\n")

    os.replace(temp_path, db_path)

