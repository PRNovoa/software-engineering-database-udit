import os
import re

DEFAULT_MAX_SIZE = 1024 * 1024  # 1 MB
SEGMENT_PATTERN = re.compile(r"^segment-(\d{6})(?:-(\d{6}))?\.log$")


def segment_name(number: int) -> str:
    """Return the file name of a single segment, e.g. segment-000001.log."""
    return f"segment-{number:06d}.log"

def parse_segment_name(name: str) -> tuple[int, int] | None:
    """Return the (first, last) numbers of a segment file name, or None if it isn't one."""
    match = SEGMENT_PATTERN.match(name)
    if match is None:
        return None
    first = int(match.group(1))
    last = int(match.group(2) or match.group(1))
    return first, last

def list_segments(directory: str | os.PathLike[str]) -> list[str]:
    """Return the segment file names in the directory, sorted by number."""
    found = []
    for name in os.listdir(directory):
        numbers = parse_segment_name(name)
        if numbers is not None:
            found.append((numbers, name))
    found.sort()
    return [name for _, name in found]

def truncate_incomplete_line(path: str | os.PathLike[str]) -> None:
    """Cut everything after the last newline, so a write cut by a crash is dropped."""
    with open(path, "r+b") as segment:
        data = segment.read()
        end = data.rfind(b"\n") + 1
        if end != len(data):
            segment.truncate(end)
            segment.flush()
            os.fsync(segment.fileno())
            
class SegmentedLog:
    """Append-only log split into segments. It behaves like a file, so entries.py works unchanged."""
    
    def __init__(self, directory: str | os.PathLike[str], max_size: int = DEFAULT_MAX_SIZE):
        self.directory = directory
        self.max_size = max_size
        os.makedirs(directory, exist_ok=True)

        segments = list_segments(directory)
        if not segments:
            self.number = 1
        else:
            numbers = parse_segment_name(segments[-1])
            assert numbers is not None  # list_segments() only returns valid names
            first, last = numbers
            if first != last:
                self.number = last + 1
            else:
                self.number = last
                truncate_incomplete_line(self._path())

        self._open()
        if self.size >= self.max_size:
            self._rotate()
        
    def _path(self) -> str:
        """Path of the active segment."""
        return os.path.join(self.directory, segment_name(self.number))
    
    def _open(self) -> None:
        """Open the active segment for appending and read its current size."""
        self._file = open(self._path(), "ab")
        self.size = self._file.tell()
    
    def _rotate(self) -> None:
        """Close the active segment and start the next one."""
        self.flush()
        os.fsync(self._file.fileno())
        self._file.close()
        self.number += 1
        self._open()
        
    def write(self, text: str) -> int:
        """Append a record, moving to a new segment first if it would not fit."""
        data = text.encode("utf-8")
        if self.size > 0 and self.size + len(data) > self.max_size:
            self._rotate()
        self._file.write(data)
        self.size += len(data)
        return len(text)
    
    def flush(self) -> None:
        """Flush the active segment."""
        self._file.flush()

    def fileno(self) -> int:
        """File descriptor of the active segment, used by db_sync() for fsync."""
        return self._file.fileno()

    def close(self) -> None:
        """Close the active segment."""
        self._file.close()

    @property
    def closed(self) -> bool:
        """Whether the active segment is closed, used by close_db()."""
        return self._file.closed