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
    temp_path = None
    temp_fd = None

    db.seek(0)
    lines = db.readlines()

    if lines and not lines[-1].endswith("\n"):
        lines.pop()

    for i in range(10):
            attempt = f"{db.name}.{os.urandom(8).hex()}.tmp"
            try:
                temp_fd = os.open(
                    attempt,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
                temp_path = attempt
                break

            except FileExistsError:
                pass

    if temp_fd is None:
        raise FileExistsError

    try:
        with open_db(temp_fd, "w") as db_temp:
            temp_fd = None

            for line in reversed(lines):
                key, value = line.rstrip("\n").split(":", 1)
                if key not in temp_cache:
                    temp_cache[key] = value

            for key, value in reversed(temp_cache.items()):
                if value != TOMBSTONE_VALUE:
                    db_temp.write(f"{key}:{value}\n")

            db_temp.flush()
            os.fsync(db_temp.fileno())

        db.close()
        os.replace(temp_path, db.name)

    finally:
        if temp_fd is not None:
            os.close(temp_fd)

        if os.path.exists(temp_path):
            os.unlink(temp_path)