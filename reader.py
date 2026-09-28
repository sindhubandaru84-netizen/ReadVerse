import html

import streamlit as st
import streamlit.components.v1 as components

from books import (
    BookSearchError,
    fetch_gutenberg_text,
    paginate,
    search_books,
    search_gutenberg,
)
from important import explain_pdf


# ---- cached wrappers so button clicks (which rerun the script) don't re-download ----

@st.cache_data(ttl=3600, show_spinner=False)
def cached_search_all(query):
    return search_books(query, max_results=12)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_search_free(query):
    return search_gutenberg(query, max_results=12)


@st.cache_data(ttl=86400, show_spinner=False)
def cached_book_pages(text_url):
    return paginate(fetch_gutenberg_text(text_url))


# ---- reader UI ----

def _close_reader():
    st.session_state.pop("reading_book", None)


def _go(delta, total, key):
    st.session_state[key] = max(1, min(total, st.session_state.get(key, 1) + delta))


def render_reader(book):
    st.button("← Back", on_click=_close_reader)

    title = html.escape(book["title"])
    authors = html.escape(", ".join(book["authors"]))
    st.html(f"""
    <div class="page-title">{title}</div>
    <div class="page-subtitle">{authors}</div>
    """)

    if book.get("read_type") == "embed":
        # Google Books embedded viewer (previews / full view depending on the book)
        components.iframe(
            f"https://books.google.com/books?id={book['id']}&pg=PP1&output=embed",
            height=760,
            scrolling=True,
        )
        st.caption("Google Books shows only the pages the publisher allows.")
        if book.get("preview_link"):
            st.link_button("Open on Google Books", book["preview_link"])
        return

    # Full-text reader (Project Gutenberg)
    try:
        with st.spinner("Loading book..."):
            pages = cached_book_pages(book["text_url"])
    except Exception as e:
        st.error(f"Could not load this book: {e}")
        return

    if not pages:
        st.warning("This book has no readable text.")
        return

    total = len(pages)
    page_key = f"page_{book['id']}"
    st.session_state.setdefault(page_key, 1)

    prev_col, mid_col, next_col = st.columns([1, 4, 1])
    with prev_col:
        st.button("◀ Prev", key="prev_top", on_click=_go, args=(-1, total, page_key),
                  use_container_width=True, disabled=st.session_state[page_key] <= 1)
    with next_col:
        st.button("Next ▶", key="next_top", on_click=_go, args=(1, total, page_key),
                  use_container_width=True, disabled=st.session_state[page_key] >= total)
    with mid_col:
        if total > 1:
            st.slider("Page", 1, total, key=page_key, label_visibility="collapsed")
        st.caption(f"Page {st.session_state[page_key]} of {total}")

    page_paragraphs = pages[st.session_state[page_key] - 1]
    body = "".join(f"<p style='margin:0 0 14px 0'>{html.escape(p)}</p>" for p in page_paragraphs)
    st.html(f"""
    <div style="background:white;border:1px solid #edf0f7;border-radius:14px;
                padding:28px 34px;font-family:Georgia,serif;font-size:17px;
                line-height:1.75;color:#26365f;">
        {body}
    </div>
    """)

    b1, b2 = st.columns(2)
    with b1:
        st.button("◀ Prev", key="prev_bottom", on_click=_go, args=(-1, total, page_key),
                  use_container_width=True, disabled=st.session_state[page_key] <= 1)
    with b2:
        st.button("Next ▶", key="next_bottom", on_click=_go, args=(1, total, page_key),
                  use_container_width=True, disabled=st.session_state[page_key] >= total)

    # Tie into ReadVerse's AI features
    if st.button("Explain this page simply"):
        with st.spinner("Explaining..."):
            try:
                st.markdown(explain_pdf("\n\n".join(page_paragraphs)))
            except Exception as e:
                st.error(f"Could not generate an explanation: {e}")