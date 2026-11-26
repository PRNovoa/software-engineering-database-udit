import pytest

from src.database import close_db
from src.entries import create_entry
from src.segments import SegmentedLog, list_segments, parse_segment_name, segment_name


def read_segment(directory, number):
    """Return the raw bytes of a single segment."""
    return (directory / segment_name(number)).read_bytes()


@pytest.mark.parametrize("name,expected", [
    pytest.param("segment-000003.log", (3, 3), id="single segment"),
    pytest.param("segment-000001-000004.log", (1, 4), id="merged segment"),
    pytest.param("segment-000003.log.a1b2.tmp", None, id="temporary file"),
    pytest.param("LOCK", None, id="other file"),
])
def test_parse_segment_name(name, expected):
    """parse_segment_name() returns the (first, last) numbers, or None for other files."""
    assert parse_segment_name(name) == expected


def test_segment_name_round_trip():
    """A name built by segment_name() is read back with the same number."""
    assert parse_segment_name(segment_name(7)) == (7, 7)


def test_list_segments_sorts_by_number_and_ignores_other_files(tmp_path):
    """list_segments() keeps only segment files, sorted by their first number."""
    for name in ["segment-000003.log", "segment-000001-000002.log", "LOCK", "segment-000003.log.a1b2.tmp"]:
        (tmp_path / name).touch()

    assert list_segments(tmp_path) == ["segment-000001-000002.log", "segment-000003.log"]


def test_empty_directory_starts_first_segment(tmp_path):
    """Opening an empty directory creates segment-000001.log."""
    log = SegmentedLog(tmp_path)
    log.close()

    assert list_segments(tmp_path) == ["segment-000001.log"]


def test_writing_more_than_max_size_creates_second_segment(tmp_path):
    """When a record doesn't fit in the active segment, it goes to a new one."""
    log = SegmentedLog(tmp_path, max_size=10)
    for line in ["a:1\n", "b:2\n", "c:3\n"]:
        log.write(line)
    log.close()

    assert read_segment(tmp_path, 1) == b"a:1\nb:2\n"
    assert read_segment(tmp_path, 2) == b"c:3\n"


def test_closed_segments_dont_change_after_new_writes(tmp_path):
    """Once a segment is closed, later writes never modify it."""
    log = SegmentedLog(tmp_path, max_size=10)
    for line in ["a:1\n", "b:2\n", "c:3\n"]:
        log.write(line)
    closed_segment = read_segment(tmp_path, 1)

    for line in ["d:4\n", "e:5\n"]:
        log.write(line)
    log.close()

    assert read_segment(tmp_path, 1) == closed_segment


def test_size_is_measured_in_bytes(tmp_path):
    """The limit counts UTF-8 bytes, so "é" takes two."""
    log = SegmentedLog(tmp_path, max_size=9)
    log.write("k:é\n")  # 5 bytes, 4 characters
    log.write("k:é\n")  # 10 bytes in total, more than 9
    log.close()

    assert list_segments(tmp_path) == ["segment-000001.log", "segment-000002.log"]


def test_record_larger_than_max_size_goes_alone(tmp_path):
    """A record bigger than the limit is written alone in its own segment."""
    log = SegmentedLog(tmp_path, max_size=5)
    log.write("name:pablo\n")
    log.write("a:1\n")
    log.close()

    assert read_segment(tmp_path, 1) == b"name:pablo\n"
    assert read_segment(tmp_path, 2) == b"a:1\n"



def test_reopening_keeps_writing_to_last_segment_if_not_full(tmp_path):
    """After a restart, new writes go to the last segment while it has room."""
    log = SegmentedLog(tmp_path, max_size=10)
    log.write("a:1\n")
    log.close()

    log = SegmentedLog(tmp_path, max_size=10)
    log.write("b:2\n")
    log.close()

    assert list_segments(tmp_path) == ["segment-000001.log"]
    assert read_segment(tmp_path, 1) == b"a:1\nb:2\n"


def test_reopening_a_full_segment_starts_a_new_one(tmp_path):
    """If the last segment is already full on startup, writes go to the next one."""
    log = SegmentedLog(tmp_path, max_size=8)
    log.write("a:1\n")
    log.write("b:2\n")
    log.close()

    log = SegmentedLog(tmp_path, max_size=8)
    log.write("c:3\n")
    log.close()

    assert read_segment(tmp_path, 1) == b"a:1\nb:2\n"
    assert read_segment(tmp_path, 2) == b"c:3\n"


@pytest.mark.parametrize("broken_tail", [
    pytest.param(b"name:pab", id="incomplete line"),
    pytest.param(b"k:\xc3", id="cut multi-byte character"),
])
def test_incomplete_last_line_is_truncated_on_startup(tmp_path, broken_tail):
    """A line cut by a crash is removed, so the next write starts on its own line (#109)."""
    (tmp_path / segment_name(1)).write_bytes(b"a:1\n" + broken_tail)

    log = SegmentedLog(tmp_path)
    log.write("city:Paris\n")
    log.close()

    assert read_segment(tmp_path, 1) == b"a:1\ncity:Paris\n"


def test_merged_last_segment_is_not_written(tmp_path):
    """A merged segment is always closed, so writes start the next number."""
    (tmp_path / "segment-000001-000002.log").write_bytes(b"a:1\n")

    log = SegmentedLog(tmp_path)
    log.write("b:2\n")
    log.close()

    assert (tmp_path / "segment-000001-000002.log").read_bytes() == b"a:1\n"
    assert read_segment(tmp_path, 3) == b"b:2\n"



def test_works_with_create_entry_and_close_db(tmp_path):
    """SegmentedLog can be used as the db in create_entry() and close_db()."""
    log = SegmentedLog(tmp_path)
    cache = {}

    create_entry("name", "pablo", log, cache)
    close_db(log)

    assert log.closed
    assert cache == {"name": "pablo"}
    assert read_segment(tmp_path, 1) == b"name:pablo\n"