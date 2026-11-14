
class DatabaseError(Exception):
    """Base class for all database-related errors."""
    pass

class InvalidEntryError(DatabaseError, ValueError):
    """The key or value cannot be stored."""
    pass

class CompactionError(DatabaseError):
    """The compaction process failed."""
    pass