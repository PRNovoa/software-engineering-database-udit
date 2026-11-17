# Dictionary should be initialized beforehand

from src.database import TOMBSTONE_VALUE, db_sync
from src.exceptions import InvalidEntryError

    
def check_is_string(text: object) -> None:
    if not isinstance(text, str):
        raise InvalidEntryError("Key and value must be strings.")
    
def check_utf8(text: str) -> None:
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise InvalidEntryError("Key and value must be valid UTF-8 strings.") from error
    
def check_newline(text: str) -> None:
    if "\n" in text or "\r" in text:
        raise InvalidEntryError("Key and value cannot contain newline characters.")
    
def check_key_format(key: str) -> None:
    if not key:
        raise InvalidEntryError("Key cannot be empty.")
    if ":" in key:
        raise InvalidEntryError("Key cannot contain ':' character.")
    
def validate_entry(key: str, value: str, allow_tombstone: bool = False) -> None:
    for text in (key, value):
        check_is_string(text)
        check_utf8(text)
        check_newline(text)     
    
    check_key_format(key)
    if not allow_tombstone and value == TOMBSTONE_VALUE:
        raise InvalidEntryError("Tombstoned values are not allowed.")          

def create_entry(key: str, value: str, db, cache: dict[str, str], allow_tombstone=False) -> None:
    """ Create an entry in the database. """
    validate_entry(key, value, allow_tombstone)
    db.write(f"{key}:{value}\n")
    db_sync(db)
    cache[key] = value
    

def read_entry(key:str , cache: dict[str, str]) -> str | None:
    """ Read an entry from the cache. """
    return cache.get(key)

def update_entry(key:str, value:str, db, cache: dict[str, str]) -> bool: 
    """ Update an entry in the database. Returns True if the entry was updated, False if the key does not exist. """
    if entry_exists(key, cache):
        create_entry(key, value, db, cache)
        return True
    return False

def entry_exists(key:str, cache: dict[str, str]) -> bool:
    """ Check if an entry exists in the cache. """
    return key in cache

def delete_entry(key:str, db, cache: dict[str, str]) -> bool:
    """ Delete an entry from the database. Returns True if the entry was deleted, False if the key does not exist. """
    if entry_exists(key, cache):
        create_entry(key, TOMBSTONE_VALUE, db, cache, allow_tombstone=True)
        del cache[key]
        return True
    return False