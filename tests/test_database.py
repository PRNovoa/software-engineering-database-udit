import os

import pytest

from src.database import close_db, compact_db, open_db, start_db
from src.exceptions import CompactionError, DatabaseError
from unittest.mock import Mock, call


def test_open_db_accepts_path(tmp_path):
    db_path = tmp_path / "test_database.txt"

    with open_db(db_path, "w") as db:
        db.write("name:pablo\n")

    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


def test_open_db_accepts_file_descriptor(tmp_path):
    db_path = tmp_path / "test_database.txt"
    file_descriptor = os.open(
        db_path,
        os.O_CREAT | os.O_WRONLY,
        0o600,
    )

    with open_db(file_descriptor, "w") as db:
        db.write("name:pablo\n")

    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"

# Write raw content to the db file, compact it and return the path.
def compact(tmp_path, content):
    db_path = tmp_path / "test_database.txt"
    db_path.write_text(content, encoding="utf-8")
    db = open_db(str(db_path))
    try:
        compact_db(db)
    finally:
        close_db(db)
    return db_path


# A key written several times keeps only its last value.
def test_compact_keeps_last_value(tmp_path):
    db_path = compact(tmp_path, "name:pablo\nname:gonzalo\nname:ivan\nname:carlos\n")
    assert db_path.read_text(encoding="utf-8") == "name:carlos\n"


# A key whose last value is tombstoned disappears from the file.
def test_compact_removes_deleted_key(tmp_path):
    db_path = compact(tmp_path, "name:pablo\nname:tombstoned\n")
    assert db_path.read_text(encoding="utf-8") == ""


# A key that is deleted and then created again stays, with its new value.
def test_compact_keeps_recreated_key(tmp_path):
    db_path = compact(tmp_path, "name:pablo\nname:tombstoned\nname:gonzalo\n")
    assert db_path.read_text(encoding="utf-8") == "name:gonzalo\n"


# Keys that were never touched stay the same and in the same order.
def test_compact_keeps_untouched_keys_in_order(tmp_path):
    db_path = compact(tmp_path, "a:1\nb:2\nc:3\nb:tombstoned\n")
    assert db_path.read_text(encoding="utf-8") == "a:1\nc:3\n"


# An empty file stays empty and does not crash.
def test_compact_empty_file(tmp_path):
    db_path = compact(tmp_path, "")
    assert db_path.read_text(encoding="utf-8") == ""


# An unterminated final record is ignored during compaction.
def test_compact_ignores_incomplete_final_record(tmp_path):
    db_path = compact(tmp_path, "name:pablo\nname:gonzalo")
    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


# The randomized temporary file does not stay behind after compacting.
def test_compact_removes_tmp_file(tmp_path):
    db_path = compact(tmp_path, "name:pablo\nname:gonzalo\n")
    assert list(tmp_path.glob(f"{db_path.name}.*.tmp")) == []


# start_db() loads a cache that matches the compacted file.
def test_start_db_cache_matches_file(tmp_path):
    db_path = tmp_path / "test_database.txt"
    db_path.write_text("a:1\nb:2\na:3\nc:tombstoned\n", encoding="utf-8")
    db, cache = start_db(str(db_path))
    close_db(db)
    lines = db_path.read_text(encoding="utf-8").splitlines()
    assert cache == dict(line.split(":", 1) for line in lines)
    assert cache == {"b": "2", "a": "3"}


# If all 10 temporary file names collide, compaction raises CompactionError
# and the original database file is left unchanged.
def test_compact_raises_when_all_tmp_names_collide(tmp_path, monkeypatch):
    content = "name:pablo\nname:gonzalo\nother:tombstoned\n"
    db_path = tmp_path / "test_database.txt"
    db_path.write_text(content, encoding="utf-8")

    fixed_bytes = b"\x00" * 8
    colliding_tmp = tmp_path / f"{db_path.name}.{fixed_bytes.hex()}.tmp"
    colliding_tmp.write_text("", encoding="utf-8")

    attempts = []

    def fake_urandom(n):
        attempts.append(n)
        return fixed_bytes

    monkeypatch.setattr(os, "urandom", fake_urandom)

    db = open_db(str(db_path))
    try:
        with pytest.raises(CompactionError) as exc_info:
            compact_db(db)
    finally:
        close_db(db)

    assert isinstance(exc_info.value, DatabaseError)
    assert len(attempts) == 10
    assert db_path.read_text(encoding="utf-8") == content
    assert colliding_tmp.exists()
    

# close_db() flushes, then fsyncs and finally closes the file.
def test_close_db_flushes_then_syncs_then_closes(monkeypatch):
    db = Mock(closed=False)
    monkeypatch.setattr(os, "fsync", db.fsync)

    close_db(db)

    assert db.mock_calls == [
        call.flush(),
        call.fileno(),
        call.fsync(db.fileno.return_value),
        call.close(),
    ]

# If flush() fails, the error reaches the caller and the file is still closed.
def test_close_db_closes_when_flush_fails(monkeypatch):
    db = Mock(closed=False)
    db.flush.side_effect = OSError("flush failed")
    monkeypatch.setattr(os, "fsync", db.fsync)

    with pytest.raises(OSError, match="flush failed"):
        close_db(db)

    db.fsync.assert_not_called()
    db.close.assert_called_once()
    
# If os.fsync() fails, the error reaches the caller and the file is still closed.
def test_close_db_closes_when_fsync_fails(monkeypatch):
    db = Mock(closed=False)
    db.fsync.side_effect = OSError("fsync failed")
    monkeypatch.setattr(os, "fsync", db.fsync)

    with pytest.raises(OSError, match="fsync failed"):
        close_db(db)

    db.close.assert_called_once()    
