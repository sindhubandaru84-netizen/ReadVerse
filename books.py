import os
import re
import requests

GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
OPEN_LIBRARY_API = "https://openlibrary.org/search.json"
HEADERS = {"User-Agent": "ReadVerse/1.0 (student project)"}

MOOD_QUERIES = {
    "Happy": "feel good uplifting fiction humor",
    "Calm": "cozy calming fiction nature quiet",
    "Motivated": "motivational success habits self help",
    "Emotional": "emotional literary fiction drama",
    "Curious": "popular science mystery nonfiction",
    "Romantic": "romance novel love story",
    "Looking for personal growth": "personal growth self improvement psychology",
}


class BookSearchError(Exception):
    """Raised when every book source failed (network / quota / API error)."""


def _search_google(query, max_results):
    params = {"q": query, "maxResults": max_results, "printType": "books"}
    key = os.getenv("GOOGLE_BOOKS_API_KEY")  # optional, avoids shared-quota 429s
    if key:
        params["key"] = key

    response = requests.get(GOOGLE_BOOKS_API, params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()
    results = []

    for item in response.json().get("items", []):
        info = item.get("volumeInfo", {})
        access = item.get("accessInfo", {}) or {}
        can_embed = bool(access.get("embeddable")) and access.get("viewability") in ("PARTIAL", "ALL_PAGES")
        links = info.get("imageLinks", {}) or {}
        thumb = (links.get("thumbnail") or links.get("smallThumbnail") or "")
        results.append({
            "id": item.get("id", ""),
            "title": info.get("title") or "Untitled",
            "authors": info.get("authors") or ["Unknown Author"],
            "description": info.get("description") or "No description available.",
            "thumbnail": thumb.replace("http://", "https://"),
            "published_date": info.get("publishedDate", ""),
            "categories": info.get("categories") or [],
            "rating": info.get("averageRating"),
            "page_count": info.get("pageCount"),
            "preview_link": info.get("previewLink", ""),
            "source": "google",
            "readable": can_embed,
            "read_type": "embed" if can_embed else "",
        })
    return results


def _search_open_library(query, max_results):
    params = {
        "q": query,
        "limit": max_results,
        "fields": "key,title,author_name,first_publish_year,cover_i,subject,"
                  "number_of_pages_median,ratings_average,first_sentence",
    }
    response = requests.get(OPEN_LIBRARY_API, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    results = []

    for doc in response.json().get("docs", []):
        cover = doc.get("cover_i")
        first_sentence = doc.get("first_sentence") or []
        rating = doc.get("ratings_average")
        results.append({
            "id": "ol" + doc.get("key", "").replace("/works/", "_"),
            "title": doc.get("title") or "Untitled",
            "authors": doc.get("author_name") or ["Unknown Author"],
            "description": first_sentence[0] if first_sentence else "No description available.",
            "thumbnail": f"https://covers.openlibrary.org/b/id/{cover}-M.jpg" if cover else "",
            "published_date": str(doc.get("first_publish_year", "")),
            "categories": (doc.get("subject") or [])[:3],
            "rating": round(rating, 1) if rating else None,
            "page_count": doc.get("number_of_pages_median"),
            "preview_link": f"https://openlibrary.org{doc['key']}" if doc.get("key") else "",
            "source": "openlibrary",
            "readable": False,
            "read_type": "",
        })
    return results


def search_books(query, max_results=12):
    """
    Search Google Books, falling back to Open Library if Google fails or
    returns nothing. Returns [] only when the search genuinely found nothing;
    raises BookSearchError when the sources could not be reached.
    """
    if not query or not query.strip():
        return []
    query = query.strip()

    errors = []
    for source in (_search_google, _search_open_library):
        try:
            results = source(query, max_results)
            if results:
                return results
        except (requests.RequestException, ValueError) as e:
            errors.append(f"{source.__name__}: {e}")

    if len(errors) == 2:
        raise BookSearchError(" | ".join(errors))
    return []


def search_books_by_mood(mood, max_results=12):
    return search_books(MOOD_QUERIES.get(mood, mood), max_results=max_results)



# ---------------------------------------------------------------------
# PROJECT GUTENBERG (free, full-text, public-domain books)
# ---------------------------------------------------------------------
GUTENDEX_API = "https://gutendex.com/books/"


def search_gutenberg(query, max_results=12):
    """Search Project Gutenberg (via Gutendex). Every result is fully readable."""
    if not query or not query.strip():
        return []

    response = requests.get(GUTENDEX_API, params={"search": query.strip()},
                            headers=HEADERS, timeout=15)
    response.raise_for_status()
    results = []

    for b in response.json().get("results", [])[:max_results]:
        formats = b.get("formats", {})
        text_url = next((u for k, u in formats.items() if k.startswith("text/plain")), "")
        if not text_url:
            continue  # no plain-text edition, can't render it in-app

        authors = []
        for a in b.get("authors", []):
            name = a.get("name", "")
            if "," in name:  # "Austen, Jane" -> "Jane Austen"
                last, first = [x.strip() for x in name.split(",", 1)]
                name = f"{first} {last}"
            authors.append(name)

        results.append({
            "id": f"pg_{b['id']}",
            "title": b.get("title") or "Untitled",
            "authors": authors or ["Unknown Author"],
            "description": "Free public-domain book from Project Gutenberg. "
                           + ("Subjects: " + "; ".join(b.get("subjects", [])[:4]) if b.get("subjects") else ""),
            "thumbnail": formats.get("image/jpeg", ""),
            "published_date": "",
            "categories": [s.split(" -- ")[0] for s in b.get("subjects", [])[:2]],
            "rating": None,
            "page_count": None,
            "preview_link": f"https://www.gutenberg.org/ebooks/{b['id']}",
            "source": "gutenberg",
            "readable": True,
            "read_type": "text",
            "text_url": text_url,
        })
    return results


def _gutenberg_candidate_urls(text_url):
    """The original URL first, then direct/mirror URLs for the same book."""
    urls = [text_url]
    m = re.search(r"/(?:ebooks|files|cache/epub)/(\d+)", text_url)
    if m:
        book_id = m.group(1)
        urls += [
            f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
            f"https://gutenberg.pglaf.org/cache/epub/{book_id}/pg{book_id}.txt",
            f"https://aleph.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
            f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8",
        ]
    seen, unique = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def fetch_gutenberg_text(text_url):
    """Download a Gutenberg plain-text book and strip the license header/footer.

    Tries several URLs/mirrors with retries, because gutenberg.org can be slow
    or unreachable from some networks.
    """
    last_error = None
    response = None
    for url in _gutenberg_candidate_urls(text_url):
        for _attempt in range(2):
            try:
                # (connect timeout, read timeout)
                response = requests.get(url, headers=HEADERS, timeout=(8, 60))
                response.raise_for_status()
                break
            except requests.RequestException as e:
                last_error = e
                response = None
        if response is not None:
            break

    if response is None:
        raise requests.RequestException(
            f"Could not reach Project Gutenberg or its mirrors ({last_error})"
        )

    response.encoding = "utf-8"
    text = response.text.replace("\r\n", "\n")

    start = re.search(r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", text, re.I | re.S)
    if start:
        text = text[start.end():]
    end = re.search(r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG EBOOK", text, re.I)
    if end:
        text = text[:end.start()]
    return text.strip()


def paginate(text, page_chars=2500):
    """Reflow hard-wrapped text into paragraphs and group them into pages."""
    paragraphs = [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    paragraphs = [p for p in paragraphs if p]

    pages, current, size = [], [], 0
    for p in paragraphs:
        if current and size + len(p) > page_chars:
            pages.append(current)
            current, size = [], 0
        current.append(p)
        size += len(p)
    if current:
        pages.append(current)
    return pages