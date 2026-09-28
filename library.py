import json
import os

LIBRARY_FILE = "library.json"


def load_library():
    """Return the list of saved books, or an empty list if none exist yet."""
    if not os.path.exists(LIBRARY_FILE):
        return []
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_library(books):
    with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, indent=2)


def is_in_library(book_id):
    return any(b.get("id") == book_id for b in load_library())


def add_book(book):
    """Add a book to the library if it isn't already saved (matched by id)."""
    library = load_library()
    if not any(b.get("id") == book.get("id") for b in library):
        library.append(book)
        save_library(library)
    return library


def remove_book(book_id):
    library = load_library()
    library = [b for b in library if b.get("id") != book_id]
    save_library(library)
    return library