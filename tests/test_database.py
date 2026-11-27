import os
from unittest.mock import Mock, call, patch

import pytest

from src.database import close_db, compact_db, create_cache, db_sync, open_db, start_db
from src.exceptions import CompactionError, DatabaseError
from src.entries import create_entry


def test_open_db_accepts_path(tmp_path):
    """open_db() accepts a filesystem path and writes to that file."""
    db_path = tmp_path / "test_database.txt"

    with open_db(db_path, "w") as db:
        db.write("name:pablo\n")

    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


def test_open_db_accepts_file_descriptor(tmp_path):
    """open_db() accepts an already open file descriptor and writes through it."""
    db_path = tmp_path / "test_database.txt"
    file_descriptor = os.open(
        db_path,
        os.O_CREAT | os.O_WRONLY,
        0o600,
    )

    with open_db(file_descriptor, "w") as db:
        db.write("name:pablo\n")

    assert db_path.read_text(encoding="utf-8") == "name:pablo\n"

def compact(tmp_path, content):
    """Write raw content to the db file, compact it and return the path."""
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
    """Compacting the file leaves only the latest live value of each key."""
    db_path = compact(tmp_path, content)
    assert db_path.read_text(encoding="utf-8") == expected


def test_compact_removes_tmp_file(tmp_path):
    """The randomized temporary file does not stay behind after compacting."""
    db_path = compact(tmp_path, "name:pablo\nname:gonzalo\n")
    assert list(tmp_path.glob(f"{db_path.name}.*.tmp")) == []


def test_start_db_cache_matches_file(tmp_path):
    """start_db() returns a usable file and preserves entries after restarting."""
    db_path = tmp_path / "test_database.txt"
    db_path.write_text("a:1\nb:2\na:3\nc:tombstoned\n", encoding="utf-8")
    db, cache = start_db(str(db_path))
    try:
        assert not db.closed
        lines = db_path.read_text(encoding="utf-8").splitlines()
        assert cache == dict(line.split(":", 1) for line in lines)
        assert cache == {"b": "2", "a": "3"}
        create_entry("d", "4", db, cache)
    finally:
        close_db(db)

    db, cache = start_db(str(db_path))
    try:
        assert not db.closed
        lines = db_path.read_text(encoding="utf-8").splitlines()
        assert cache == dict(line.split(":", 1) for line in lines)
        assert cache == {"b": "2", "a": "3", "d": "4"}
    finally:
        close_db(db)


def test_db_sync_flushes_and_syncs(tmp_path):
    """db_sync() flushes pending writes to the file and calls os.fsync() on it."""
    db_path = tmp_path / "test_database.txt"

    with open_db(db_path) as db:
        db.write("name:pablo\n")
        with patch("src.database.os.fsync", wraps=os.fsync) as sync:
            db_sync(db)

            sync.assert_called_once_with(db.fileno())
            assert db_path.read_text(encoding="utf-8") == "name:pablo\n"


def test_failed_compaction_preserves_database(tmp_path):
    """If compaction fails, the original database is unchanged and no temporary file is left behind."""
    db_path = tmp_path / "test_database.tmp"
    original = "name:pablo\nname:new\nage:30\nage:tombstoned\n"
    db_path.write_text(original, encoding="utf-8")

    with open_db(db_path) as db:
        with patch("src.database.os.fsync", side_effect=OSError("sync failed")):
            with pytest.raises(OSError, match="sync failed"):
                compact_db(db)

    assert db_path.read_text(encoding="utf-8") == original
    assert list(tmp_path.glob("test_database.tmp.*.tmp")) == []

def test_compact_raises_when_all_tmp_names_collide(tmp_path, monkeypatch):
    """If all 10 temporary file names collide, compaction raises CompactionError
    and the original database file is left unchanged.
    """
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


def test_close_db_flushes_then_syncs_then_closes(monkeypatch):
    """close_db() flushes, then fsyncs and finally closes the file."""
    db = Mock(closed=False)
    monkeypatch.setattr(os, "fsync", db.fsync)

    close_db(db)

    assert db.mock_calls == [
        call.flush(),
        call.fileno(),
        call.fsync(db.fileno.return_value),
        call.close(),
    ]

def test_close_db_closes_when_flush_fails(monkeypatch):
    """If flush() fails, the error reaches the caller and the file is still closed."""
    db = Mock(closed=False)
    db.flush.side_effect = OSError("flush failed")
    monkeypatch.setattr(os, "fsync", db.fsync)

    with pytest.raises(OSError, match="flush failed"):
        close_db(db)

    db.fsync.assert_not_called()
    db.close.assert_called_once()

def test_close_db_closes_when_fsync_fails(monkeypatch):
    """If os.fsync() fails, the error reaches the caller and the file is still closed."""
    db = Mock(closed=False)
    db.fsync.side_effect = OSError("fsync failed")
    monkeypatch.setattr(os, "fsync", db.fsync)

    with pytest.raises(OSError, match="fsync failed"):
        close_db(db)

    db.close.assert_called_once()

def test_open_db_preserves_contents_and_appends(tmp_path):
    """open_db() preserves existing contents and appends new data."""
    db_path = tmp_path / "test_database.txt"
    db_path.write_text("name:pablo\n", encoding="utf-8")

    with open_db(db_path) as db:
        db.write("city:Madrid\n")
        db.seek(0)
        db.write("age:25\n")

    assert db_path.read_text(encoding="utf-8") == "name:pablo\ncity:Madrid\nage:25\n"


def test_create_cache_rewinds_and_preserves_values(tmp_path):
    """create_cache() rewinds and preserves empty and Unicode values."""
    db_path = tmp_path / "test_database.txt"
    db_path.write_text("empty:\nciudad:Aragón\n", encoding="utf-8")

    with open_db(db_path) as db:
        db.seek(0)
        db.readline()
        cache = create_cache(db)

    assert cache == {"empty": "", "ciudad": "Aragón"}

def test_start_db_closes_file_when_compaction_fails(tmp_path):
    """start_db() closes the file and propagates compaction errors."""
    db_path = tmp_path / "test_database.txt"
    db_path.write_text("name:pablo\n", encoding="utf-8")
    db = open_db(db_path)
    error = OSError("compaction failed")

    try:
        with (
            patch("src.database.open_db", return_value=db),
            patch("src.database.compact_db", side_effect=error),
            pytest.raises(OSError) as exc_info,
        ):
            start_db(str(db_path))

        assert exc_info.value is error
        assert db.closed
    finally:
        db.close()
