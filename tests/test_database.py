import os
from unittest.mock import patch

import pytest

from src.database import close_db, compact_db, db_sync, open_db, start_db
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
    db_path = tmp_path / "test_database.tmp"
    db_path.write_text(content, encoding="utf-8")
    db = open_db(str(db_path))
    try:
        compact_db(db)
    finally:
        close_db(db)
    return db_path


COMPACTION_TESTS = [ 
    pytest.param("name:pablo\nname:gonzalo\nname:ivan\nname:carlos\n", "name:carlos\n", id="keeps last value"),
    pytest.param("name:pablo\nname:tombstoned\n", "", id="removes deleted key"),
    pytest.param("name:pablo\nname:tombstoned\nname:gonzalo\n", "name:gonzalo\n", id="keeps recreated key"),
    pytest.param("a:1\nb:2\nc:3\nb:tombstoned\n", "a:1\nc:3\n", id="keeps untouched keys in order"),
    pytest.param("", "", id="empty file"),
    pytest.param("name:pablo\nname:gonzalo", "name:pablo\n", id="ignores incomplete final record"),
]

@pytest.mark.parametrize("content,expected", COMPACTION_TESTS)
def test_compact(tmp_path, content, expected):
    db_path = compact(tmp_path, content)
    assert db_path.read_text(encoding="utf-8") == expected


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


def test_db_sync_flushes_and_syncs(tmp_path):
    db_path = tmp_path / "test_database.txt"

    with open_db(db_path) as db:
        db.write("name:pablo\n")
        with patch("src.database.os.fsync", wraps=os.fsync) as sync:
            db_sync(db)

            sync.assert_called_once_with(db.fileno())
            assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


def test_failed_compaction_preserves_database(tmp_path):
    db_path = tmp_path / "test_database.tmp"
    original = "name:pablo\nname:new\nage:30\nage:tombstoned\n"
    db_path.write_text(original, encoding="utf-8")

    with open_db(db_path) as db:
        with patch("src.database.os.fsync", side_effect=OSError("sync failed")):
            with pytest.raises(OSError, match="sync failed"):
                compact_db(db)

    assert db_path.read_text(encoding="utf-8") == original
    assert list(tmp_path.glob("test_database.tmp.*.tmp")) == []

# If all 10 temporary file names collide, compaction raises CompactionError
# and the original database file is left unchanged.
def test_compact_raises_when_all_tmp_names_collide(tmp_path, monkeypatch):
    content = "name:pablo\nname:gonzalo\nother:tombstoned\n"
    db_path = tmp_path / "test_database.tmp"
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
