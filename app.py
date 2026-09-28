import streamlit as st
import json
import html
import hashlib

from extract import extract_text
from chunk import split_text
from embeddings import create_embeddings
from vector_store import create_index, search_index
from important import explain_topic, explain_pdf, generate_mcqs
from books import search_books, search_books_by_mood, BookSearchError
from reader import render_reader, cached_search_all, cached_search_free
from library import load_library, add_book, remove_book


# ---------------------------------------------------------
# SHARED: BOOK RESULT GRID
# ---------------------------------------------------------

def render_book_grid(results, cols_per_row=4, action_label=None, on_action=None, key_prefix="grid"):
    """
    Render a responsive grid of book cards with a details expander each.

    If action_label and on_action are given, an extra button is shown
    inside each book's expander (used for "Save to Library" /
    "Remove from Library"). on_action receives the book dict.
    """
    for row_start in range(0, len(results), cols_per_row):
        row_books = results[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)

        for col_offset, (col, book) in enumerate(zip(cols, row_books)):
            with col:
                title = html.escape(book["title"])
                authors = html.escape(", ".join(book["authors"]))
                rating = book.get("rating")
                rating_html = f"⭐ {rating}" if rating else "&nbsp;"
                thumb = book.get("thumbnail") or ""

                if thumb:
                    cover_html = (
                        f'<img src="{html.escape(thumb)}" '
                        'style="width:100%;height:170px;object-fit:cover;'
                        'border-radius:8px;display:block;">'
                    )
                else:
                    cover_html = (
                        '<div style="width:100%;height:170px;border-radius:8px;'
                        'background:#eef1fb;display:flex;align-items:center;'
                        'justify-content:center;color:#a7b2d6;font-size:11px;">'
                        'No cover</div>'
                    )

                st.html(f"""
                <div style="
                    background:white;
                    border:1px solid #edf0f7;
                    border-radius:14px;
                    padding:10px;
                    margin-bottom:10px;
                ">
                    {cover_html}
                    <div style="
                        font-size:12px;
                        font-weight:700;
                        color:#27365d;
                        margin-top:8px;
                        line-height:1.35;
                        min-height:32px;
                    ">{title}</div>
                    <div style="
                        font-size:10px;
                        color:#8a96af;
                        margin-top:2px;
                    ">{authors}</div>
                    <div style="
                        font-size:10px;
                        color:#e2a239;
                        margin-top:4px;
                    ">{rating_html}</div>
                </div>
                """)

                if book.get("readable"):
                    if st.button("📖 Read",
                                 key=f"{key_prefix}_read_{book.get('id', '')}_{row_start + col_offset}",
                                 use_container_width=True, type="primary"):
                        st.session_state["reading_book"] = book
                        st.rerun()
                else:
                    st.caption("No readable copy available")

                with st.expander("Details"):
                    description = book.get("description") or "No description available."
                    if len(description) > 500:
                        description = description[:500] + "..."
                    st.write(description)

                    if book.get("published_date"):
                        st.caption(f"Published: {book['published_date']}")
                    if book.get("page_count"):
                        st.caption(f"Pages: {book['page_count']}")
                    if book.get("categories"):
                        st.caption("Genre: " + ", ".join(book["categories"]))
                    if book.get("preview_link"):
                        st.link_button(
                            "Preview on Google Books",
                            book["preview_link"],
                            use_container_width=True
                        )

                    if action_label and on_action:
                        button_key = f"{key_prefix}_{action_label}_{book.get('id', '')}_{row_start + col_offset}"
                        if st.button(action_label, key=button_key, use_container_width=True):
                            on_action(book)
                            st.rerun()


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="ReadVerse",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.html("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*{
    font-family: 'Inter', sans-serif;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #f8faff;
}

/* Remove Streamlit top spacing */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}

/* Hide top toolbar */
[data-testid="stToolbar"] {
    display: none;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* ---------------------------------------------------------
   SIDEBAR
--------------------------------------------------------- */

section[data-testid="stSidebar"] {
    background: #f4f7ff !important;
    border-right: 1px solid #e8edfa;
}

section[data-testid="stSidebar"] > div {
    padding: 0 !important;
}

section[data-testid="stSidebar"] .block-container {
    padding: 25px 18px !important;
}

/* Logo */
.logo-area {
    padding: 4px 10px 22px 10px;
}

.logo-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

.logo-icon {
    width: 35px;
    height: 35px;
    border-radius: 9px;
    background: linear-gradient(135deg, #746cff, #4d7cff);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 5px 15px rgba(87, 105, 255, 0.20);
}

.logo-text {
    font-size: 17px;
    font-weight: 800;
    color: #172b67;
    letter-spacing: -0.4px;
}

.logo-subtitle {
    font-size: 8px;
    color: #8792b0;
    margin-top: 1px;
    letter-spacing: 0.3px;
}

/* Sidebar radio */
section[data-testid="stSidebar"] [data-testid="stRadio"] {
    margin-top: 2px;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] > label {
    display: none;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
    gap: 6px;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    border-radius: 12px;
    padding: 10px 12px;
    transition: all 0.2s ease;
    color: #22325e !important;
    font-size: 12px;
    font-weight: 500;
    border: 1px solid transparent;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #edf2ff;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label p {
    color: #22325e !important;
    font-size: 12px !important;
    margin: 0 !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {
    background: #e9efff;
    color: #2463ff !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] p {
    color: #2463ff !important;
    font-weight: 600;
}

/* Hide radio circles */
section[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
    display: none;
}

/* Sidebar bottom card */
.sidebar-bottom {
    margin: 115px 4px 0 4px;
    padding: 18px 15px;
    border-radius: 14px;
    background: linear-gradient(145deg, #eaf0ff, #f0e8ff);
    min-height: 125px;
    position: relative;
    overflow: hidden;
}

.sidebar-star {
    color: #667dff;
    font-size: 18px;
}

.sidebar-bottom-title {
    color: #263663;
    font-size: 11px;
    font-weight: 700;
    margin-top: 8px;
}

.sidebar-bottom-text {
    color: #8791ad;
    font-size: 8px;
    margin-top: 5px;
}

.sidebar-wave {
    position: absolute;
    left: -15px;
    right: -15px;
    bottom: -20px;
    height: 45px;
    background: linear-gradient(
        90deg,
        rgba(130, 190, 255, 0.55),
        rgba(185, 143, 255, 0.45)
    );
    border-radius: 50% 50% 0 0;
}


/* ---------------------------------------------------------
   MAIN FORM CONTROLS
--------------------------------------------------------- */

[data-testid="stRadio"] label {
    color: #26365f !important;
}

[data-testid="stRadio"] label p {
    color: #26365f !important;
    font-size: 14px !important;
}

[data-testid="stRadio"] [role="radiogroup"] label,
[data-testid="stRadio"] [role="radiogroup"] label *,
[data-testid="stRadio"] [role="radiogroup"] label div,
[data-testid="stRadio"] [role="radiogroup"] label span {
    color: #26365f !important;
}

[data-testid="stRadio"] [role="radiogroup"] label {
    background: transparent !important;
}

[data-testid="stRadio"] [role="radiogroup"] {
    gap: 10px !important;
}

div[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: #26365f !important;
    -webkit-text-fill-color: #26365f !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #8a95ad !important;
    opacity: 1 !important;
}

/* ---------------------------------------------------------
   HERO
--------------------------------------------------------- */

.hero {
    height: 135px;
    border-radius: 14px;
    background: linear-gradient(105deg, #f0f5ff 0%, #f4f6ff 55%, #e7f1ff 100%);
    position: relative;
    overflow: hidden;
    padding: 23px 26px;
    box-sizing: border-box;
    border: 1px solid #edf1fb;
}

.welcome {
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 3px;
    color: #294c96;
    margin-bottom: 3px;
}

.hero-title {
    font-size: 40px;
    line-height: 42px;
    font-weight: 800;
    letter-spacing: -2px;
    color: #10265d;
}

.hero-title span {
    color: #5d73ff;
}

.hero-text {
    font-size: 12px;
    line-height: 18px;
    color: #7080a0;
    width: 370px;
    margin-top: 5px;
}

/* Decorative books */
.hero-books {
    position: absolute;
    right: 60px;
    bottom: 12px;
    width: 185px;
    height: 90px;
}

.book-stack {
    position: absolute;
    right: 0;
    width: 140px;
    height: 18px;
    border-radius: 5px;
    transform: rotate(-3deg);
    box-shadow: 0 6px 12px rgba(75, 99, 190, 0.18);
}

.book-one {
    bottom: 7px;
    background: linear-gradient(90deg, #6652e8, #8069ff);
}

.book-two {
    bottom: 27px;
    right: 20px;
    background: linear-gradient(90deg, #4d80ed, #74a4ff);
}

.book-three {
    bottom: 47px;
    right: 35px;
    background: linear-gradient(90deg, #8a68ef, #a58aff);
}

.hero-plant {
    position: absolute;
    right: 15px;
    bottom: 5px;
    font-size: 42px;
}

.hero-cup {
    position: absolute;
    right: 65px;
    bottom: 0;
    font-size: 34px;
}

.hero-note {
    position: absolute;
    right: 230px;
    top: 38px;
    color: #7c8cff;
    font-size: 12px;
    font-style: italic;
    transform: rotate(-7deg);
}


/* ---------------------------------------------------------
   SEARCH
--------------------------------------------------------- */

.search-area {
    margin-top: 13px;
    margin-bottom: 14px;
}

.search-label {
    font-size: 0;
}

div[data-testid="stTextInput"] {
    margin: 0 !important;
}

div[data-testid="stTextInput"] > div {
    background: #ffffff;
    border: 1.5px solid #b8c4ea;
    border-radius: 28px;
    box-shadow: 0 4px 14px rgba(67, 89, 145, 0.14);
    height: 46px;
}

div[data-testid="stTextInput"] > div:focus-within {
    border-color: #4d7cff;
    box-shadow: 0 0 0 3px rgba(77, 124, 255, 0.18);
}

div[data-testid="stTextInput"] input {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    font-size: 15px !important;
    padding-left: 18px !important;
    padding-right: 18px !important;
    color: #26365f !important;
    -webkit-text-fill-color: #26365f !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #7d89a8 !important;
    -webkit-text-fill-color: #7d89a8 !important;
    opacity: 1 !important;
}

/* Inputs inside st.form (e.g. "Ask a Question") were losing their
   white background/dark text in some browsers - force it here too. */
div[data-testid="stForm"] div[data-testid="stTextInput"] > div {
    background: #ffffff !important;
    border: 1.5px solid #b8c4ea !important;
    border-radius: 10px !important;
}

div[data-testid="stForm"] div[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: #26365f !important;
    -webkit-text-fill-color: #26365f !important;
}

.search-button button {
    border-radius: 22px !important;
    background: linear-gradient(135deg, #6374ff, #5279f5) !important;
    color: white !important;
    border: none !important;
    font-size: 10px !important;
    font-weight: 600 !important;
}


/* ---------------------------------------------------------
   FEATURE CARDS
--------------------------------------------------------- */

.feature-card {
    height: 142px;
    border-radius: 10px;
    padding: 13px;
    box-sizing: border-box;
    border: 1px solid rgba(230,235,248,0.8);
    position: relative;
}

.feature-purple {
    background: linear-gradient(145deg, #f0f1ff, #f4f2ff);
}

.feature-green {
    background: linear-gradient(145deg, #eefaf7, #effbf9);
}

.feature-pink {
    background: linear-gradient(145deg, #fff0f5, #fff4f7);
}

.feature-blue {
    background: linear-gradient(145deg, #edf5ff, #eff6ff);
}

.feature-icon {
    width: 27px;
    height: 27px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    margin-bottom: 9px;
}

.icon-purple {
    background: #e4e6ff;
    color: #6672ff;
}

.icon-green {
    background: #d9f4ed;
    color: #14a982;
}

.icon-pink {
    background: #ffddea;
    color: #ff4e9c;
}

.icon-blue {
    background: #dcecff;
    color: #3577e8;
}

.feature-title {
    font-size: 11px;
    font-weight: 700;
    color: #27365d;
    margin-bottom: 6px;
}

.feature-text {
    font-size: 8.5px;
    line-height: 13px;
    color: #8190ad;
    width: 95%;
}

.feature-arrow {
    position: absolute;
    left: 13px;
    bottom: 12px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 11px;
    background: rgba(255,255,255,0.65);
    color: #4674e8;
}


/* ---------------------------------------------------------
   POPULAR BOOKS
--------------------------------------------------------- */

.section-heading {
    margin-top: 10px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.section-title {
    font-size: 13px;
    font-weight: 800;
    color: #24345f;
}

.section-title span {
    color: #6579ff;
    margin-right: 4px;
}

.view-all {
    font-size: 9px;
    color: #4674e8;
    font-weight: 600;
}

.book-card {
    background: white;
    border-radius: 9px;
    border: 1px solid #edf0f7;
    padding: 7px;
    box-shadow: 0 4px 14px rgba(62, 82, 135, 0.07);
    min-height: 137px;
}

.book-cover {
    height: 72px;
    border-radius: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    font-size: 11px;
    font-weight: 800;
    line-height: 12px;
    padding: 5px;
    box-sizing: border-box;
    overflow: hidden;
}

.cover-atomic {
    background: linear-gradient(145deg, #fff6d9, #f6e5ba);
    color: #b48742;
}

.cover-midnight {
    background: linear-gradient(145deg, #102951, #173e72);
    color: white;
}

.cover-itends {
    background: linear-gradient(145deg, #ffe3ed, #f6a7c5);
    color: #c72869;
}

.cover-dune {
    background: linear-gradient(145deg, #e97b1b, #c84c0c);
    color: white;
}

.cover-hail {
    background: linear-gradient(145deg, #161616, #383838);
    color: white;
}

.cover-money {
    background: linear-gradient(145deg, #f4f4f2, #ffffff);
    color: #555;
}

.book-title {
    font-size: 8.5px;
    font-weight: 700;
    color: #27365d;
    margin-top: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.book-author {
    font-size: 7.5px;
    color: #8b96ae;
    margin-top: 3px;
}

.book-tag {
    display: inline-block;
    font-size: 6.5px;
    color: #6681bb;
    background: #edf4ff;
    padding: 3px 6px;
    border-radius: 10px;
    margin-top: 5px;
}


/* ---------------------------------------------------------
   CONTENT PAGES
--------------------------------------------------------- */

.page-title {
    font-size: 28px;
    font-weight: 800;
    color: #172b67;
    margin-bottom: 5px;
}

.page-subtitle {
    color: #7b89a7;
    font-size: 12px;
    margin-bottom: 20px;
}

.content-box {
    background: white;
    border-radius: 14px;
    padding: 22px;
    border: 1px solid #edf0f7;
    box-shadow: 0 5px 18px rgba(67, 89, 145, 0.06);
}


/* ---------------------------------------------------------
   STREAMLIT BUTTONS
--------------------------------------------------------- */

.stButton > button {
    border-radius: 9px;
    border: 1px solid #e1e7f5;
    background: white;
    color: #37528d;
    font-size: 12px;
    font-weight: 600;
}

.stButton > button:hover {
    border-color: #7184ff;
    color: #536bff;
}


/* ---------------------------------------------------------
   FILE UPLOADER
--------------------------------------------------------- */

[data-testid="stFileUploader"] {
    background: white;
    border-radius: 14px;
    border: 1px solid #e7ebf5;
    padding: 10px;
}


/* ---------------------------------------------------------
   RADIO / SELECT
--------------------------------------------------------- */

.stRadio > label {
    font-weight: 600 !important;
    color: #34456f !important;
}

</style>
""")


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.html("""
    <div class="logo-area">
        <div class="logo-row">
            <div class="logo-icon">
                <span style="
                    display:block;
                    width:18px;
                    height:20px;
                    border:2px solid white;
                    border-radius:2px 5px 5px 2px;
                    position:relative;
                    box-sizing:border-box;
                "></span>
            </div>
            <div>
                <div class="logo-text">ReadVerse</div>
                <div class="logo-subtitle">Read · Learn · Grow</div>
            </div>
        </div>
    </div>
    """)

    page = st.radio(
        "Navigation",
        [
            "Home",
            "Upload & Read",
            "Search Novels",
            "Mood Recommendations",
            "My Library"
        ],
        label_visibility="collapsed"
    )

    st.html("""
    <div class="sidebar-bottom">
        <div class="sidebar-star">✦</div>
        <div class="sidebar-bottom-title">
            Good books<br>
            better days
        </div>
        <div class="sidebar-bottom-text">
            Read. Learn. Grow.
        </div>
        <div class="sidebar-wave"></div>
    </div>
    """)


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

if st.session_state.get("reading_book"):
    render_reader(st.session_state["reading_book"])

elif page == "Home":

    st.html("""
    <div class="hero">
        <div class="welcome">WELCOME TO</div>
        <div class="hero-title">Read<span>Verse</span></div>
        <div class="hero-text">
            Your space to explore books, understand ideas,<br>
            and find your next favorite read.
        </div>
        <div class="hero-note">
            More books.<br>
            More perspectives.
        </div>
        <div class="hero-books">
            <div class="book-stack book-one"></div>
            <div class="book-stack book-two"></div>
            <div class="book-stack book-three"></div>
        </div>
        <div class="hero-cup"> </div>
        <div class="hero-plant"> </div>
    </div>
    """)

    st.html("""
    <div class="search-area"></div>
    """)

    col1, col2 = st.columns([5.2, 0.8], gap="small")

    with col1:
        search_text = st.text_input(
            "Search",
            placeholder="Search for a novel, author, or topic...",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
        search_clicked = st.button("Search", use_container_width=True)

    if search_clicked and search_text.strip():
        st.session_state["novel_search"] = search_text.strip()
        st.info("Open Search Novels from the sidebar to view the search.")

    st.html("""
    <div style="height:2px"></div>
    <div style="
        display:grid;
        grid-template-columns:repeat(4,1fr);
        gap:14px;
    ">
        <div class="feature-card feature-purple">
            <div class="feature-icon icon-purple">R</div>
            <div class="feature-title">Upload & Read</div>
            <div class="feature-text">
                Upload your PDF and get
                instant summaries, explanations
                and key insights.
            </div>
            <div class="feature-arrow">→</div>
        </div>

        <div class="feature-card feature-green">
            <div class="feature-icon icon-green">S</div>
            <div class="feature-title">Search Novels</div>
            <div class="feature-text">
                Find your next favorite book
                by searching titles, authors
                or genres.
            </div>
            <div class="feature-arrow">→</div>
        </div>

        <div class="feature-card feature-pink">
            <div class="feature-icon icon-pink">M</div>
            <div class="feature-title">Mood Recommendations</div>
            <div class="feature-text">
                Tell us how you feel, and get
                personalized book suggestions
                just for you.
            </div>
            <div class="feature-arrow">→</div>
        </div>

        <div class="feature-card feature-blue">
            <div class="feature-icon icon-blue">L</div>
            <div class="feature-title">My Library</div>
            <div class="feature-text">
                Save your favorite books
                and keep track of your
                reading journey.
            </div>
            <div class="feature-arrow">→</div>
        </div>
    </div>
    """)

    st.html("""
    <div class="section-heading">
        <div class="section-title">
            <span>✦</span> Popular Books
        </div>
        <div class="view-all">View all →</div>
    </div>
    """)

    books = [
        ("Atomic Habits", "James Clear", "Self Help", "cover-atomic"),
        ("The Midnight Library", "Matt Haig", "Fiction", "cover-midnight"),
        ("It Ends With Us", "Colleen Hoover", "Romance", "cover-itends"),
        ("Dune", "Frank Herbert", "Sci-Fi", "cover-dune"),
        ("Project Hail Mary", "Andy Weir", "Sci-Fi", "cover-hail"),
        ("The Psychology of Money", "Morgan Housel", "Finance", "cover-money")
    ]

    cols = st.columns(6, gap="small")
    for col, book in zip(cols, books):
        title, author, tag, cover = book
        with col:
            st.html(f"""
            <div class="book-card">
                <div class="book-cover {cover}">{html.escape(title)}</div>
                <div class="book-title">{html.escape(title)}</div>
                <div class="book-author">{html.escape(author)}</div>
                <div class="book-tag">{html.escape(tag)}</div>
            </div>
            """)


# ---------------------------------------------------------
# UPLOAD & READ
# ---------------------------------------------------------

elif page == "Upload & Read":

    st.html("""
    <div class="page-title">Upload & Read</div>
    <div class="page-subtitle">
        Upload a PDF and explore its content with ReadVerse.
    </div>
    """)

    uploaded_file = st.file_uploader(
        "Upload your PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        file_bytes = uploaded_file.getvalue()
        file_hash = hashlib.md5(file_bytes).hexdigest()

        if st.session_state.get("pdf_hash") != file_hash:
            with open("uploaded.pdf", "wb") as f:
                f.write(file_bytes)

            with st.spinner("Preparing your PDF..."):
                text = extract_text("uploaded.pdf")
                chunks = split_text(text) if text else []
                embeddings = create_embeddings(chunks) if chunks else []
                index = create_index(embeddings) if chunks else None

            st.session_state["pdf_hash"] = file_hash
            st.session_state["pdf_text"] = text
            st.session_state["chunks"] = chunks
            st.session_state["index"] = index
            st.session_state["quiz"] = None
            st.session_state["submitted"] = False
            st.session_state["score"] = 0

        text = st.session_state.get("pdf_text", "")
        chunks = st.session_state.get("chunks", [])
        index = st.session_state.get("index")

        if text:
            option = st.radio(
                "Choose an option",
                [
                    "Explain PDF",
                    "Ask a Question",
                    "Generate MCQs"
                ],
                horizontal=True
            )

            if option == "Explain PDF":

                if st.button("Explain PDF"):
                    with st.spinner("Reading and explaining your PDF..."):
                        explanation = explain_pdf(text)

                    safe_explanation = html.escape(str(explanation))
                    safe_explanation = safe_explanation.replace("\n\n", "<br><br>")
                    safe_explanation = safe_explanation.replace("\n", "<br>")

                    st.html(f"""
                    <div style="
                        background:#ffffff;
                        padding:28px;
                        margin-top:20px;
                        border-radius:16px;
                        border:1px solid #dfe5f2;
                        box-shadow:0 6px 20px rgba(50,70,120,0.08);
                    ">
                        <div style="
                            color:#172b67;
                            font-size:20px;
                            font-weight:700;
                            margin-bottom:18px;
                        ">Explanation</div>
                        <div style="
                            color:#26365f !important;
                            font-size:14px;
                            line-height:1.8;
                            font-weight:400;
                        ">{safe_explanation}</div>
                    </div>
                    """)

            elif option == "Ask a Question":

                with st.form("ask_question_form", clear_on_submit=False):
                    question = st.text_input(
                        "Question",
                        placeholder="Ask something about the PDF...",
                        label_visibility="collapsed"
                    )
                    ask_submitted = st.form_submit_button("Ask Question")

                if ask_submitted and question.strip():
                    with st.spinner("Finding the answer..."):
                        query_embedding = create_embeddings([question.strip()])
                        search_results = search_index(index, query_embedding, 3)

                        if isinstance(search_results, tuple) and len(search_results) == 2:
                            _, indices = search_results
                            if hasattr(indices, "tolist"):
                                indices = indices.tolist()
                            if indices and isinstance(indices[0], (list, tuple)):
                                indices = indices[0]
                            relevant_chunks = [
                                chunks[int(i)]
                                for i in indices
                                if 0 <= int(i) < len(chunks)
                            ]
                        else:
                            results = search_results
                            if hasattr(results, "tolist"):
                                results = results.tolist()
                            if isinstance(results, (list, tuple)) and results and isinstance(results[0], (list, tuple)):
                                results = results[0]
                            if isinstance(results, (list, tuple)) and all(
                                isinstance(x, (int, float)) and float(x).is_integer() for x in results
                            ):
                                relevant_chunks = [
                                    chunks[int(i)]
                                    for i in results
                                    if 0 <= int(i) < len(chunks)
                                ]
                            else:
                                relevant_chunks = list(results) if isinstance(results, (list, tuple)) else [str(results)]

                        context = "\n\n".join(str(chunk) for chunk in relevant_chunks)
                        answer = explain_topic(question.strip(), context)

                    safe_answer = html.escape(str(answer))
                    safe_answer = safe_answer.replace("\n\n", "<br><br>")
                    safe_answer = safe_answer.replace("\n", "<br>")

                    st.html(f"""
                    <div style="
                        background:#ffffff;
                        padding:28px;
                        margin-top:20px;
                        border-radius:16px;
                        border:1px solid #dfe5f2;
                        box-shadow:0 6px 20px rgba(50,70,120,0.08);
                    ">
                        <div style="
                            color:#172b67;
                            font-size:20px;
                            font-weight:700;
                            margin-bottom:18px;
                        ">Answer</div>
                        <div style="
                            color:#26365f;
                            font-size:14px;
                            line-height:1.8;
                        ">{safe_answer}</div>
                    </div>
                    """)

            elif option == "Generate MCQs":

                if "quiz" not in st.session_state:
                    st.session_state.quiz = None
                if "submitted" not in st.session_state:
                    st.session_state.submitted = False
                if "score" not in st.session_state:
                    st.session_state.score = 0

                def _parse_quiz_response(quiz_data):
                    # Handle normal JSON, JSON inside ```json fences,
                    # and responses containing extra text around the JSON array.
                    if isinstance(quiz_data, str):
                        raw = quiz_data.strip()
                        if raw.startswith("```json"):
                            raw = raw[7:]
                        elif raw.startswith("```"):
                            raw = raw[3:]
                        if raw.endswith("```"):
                            raw = raw[:-3]
                        raw = raw.strip()

                        start = raw.find("[")
                        end = raw.rfind("]")
                        if start != -1 and end != -1 and end > start:
                            raw = raw[start:end + 1]

                        quiz_data = json.loads(raw)

                    if isinstance(quiz_data, dict):
                        quiz_data = quiz_data.get("questions", quiz_data.get("quiz", []))

                    if not isinstance(quiz_data, list) or not quiz_data:
                        raise ValueError("No quiz questions were returned")

                    # Validate the fields needed by the UI.
                    for q in quiz_data:
                        if not isinstance(q, dict):
                            raise ValueError("Invalid question format")
                        if "question" not in q or "options" not in q or "answer" not in q:
                            raise ValueError("Each question needs question, options, and answer fields")
                        if not isinstance(q["options"], list) or len(q["options"]) < 2:
                            raise ValueError("Each question must have at least two options")

                    return quiz_data

                num_questions = st.number_input(
                    "Number of questions",
                    min_value=1,
                    max_value=25,
                    value=5,
                    step=1
                )

                gen_col1, gen_col2 = st.columns(2)
                with gen_col1:
                    generate_clicked = st.button("Generate MCQs", use_container_width=True)
                with gen_col2:
                    add_more_clicked = st.button(
                        "Add More Questions",
                        use_container_width=True,
                        disabled=not st.session_state.quiz
                    )

                if generate_clicked:
                    with st.spinner("Generating questions..."):
                        quiz_data = generate_mcqs(text, num_questions=int(num_questions))

                    try:
                        st.session_state.quiz = _parse_quiz_response(quiz_data)
                        st.session_state.submitted = False
                        st.session_state.score = 0

                    except Exception as e:
                        st.session_state.quiz = None
                        st.error(f"Could not read the generated quiz: {e}")

                if add_more_clicked and st.session_state.quiz:
                    with st.spinner("Generating more questions..."):
                        existing_questions = [q["question"] for q in st.session_state.quiz]
                        quiz_data = generate_mcqs(
                            text,
                            num_questions=int(num_questions),
                            exclude_questions=existing_questions
                        )

                    try:
                        new_questions = _parse_quiz_response(quiz_data)
                        st.session_state.quiz = st.session_state.quiz + new_questions
                        st.session_state.submitted = False

                    except Exception as e:
                        st.error(f"Could not generate more questions: {e}")

                if st.session_state.quiz:
                    quiz = st.session_state.quiz

                    st.html("""
                    <div style="
                        background:#ffffff;
                        padding:22px;
                        margin-top:20px;
                        margin-bottom:20px;
                        border-radius:16px;
                        border:1px solid #dfe5f2;
                    ">
                        <div style="
                            color:#172b67;
                            font-size:20px;
                            font-weight:700;
                        ">Quiz</div>
                    </div>
                    """)

                    for i, q in enumerate(quiz):
                        question_text = html.escape(str(q["question"]))
                        st.html(f"""
                        <div style="
                            color:#172b67;
                            font-size:15px;
                            line-height:1.6;
                            font-weight:600;
                            margin-top:18px;
                            margin-bottom:8px;
                        ">
                            {i + 1}. {question_text}
                        </div>
                        """)

                        st.radio(
                            "Choose your answer",
                            q["options"],
                            key=f"question_{i}",
                            index=None,
                            label_visibility="collapsed"
                        )

                    if st.button("Submit Quiz"):
                        score = 0
                        for i, q in enumerate(quiz):
                            answer = st.session_state.get(f"question_{i}")
                            correct_answer = q["answer"]

                            if isinstance(correct_answer, int):
                                if 0 <= correct_answer < len(q["options"]):
                                    correct_answer = q["options"][correct_answer]
                                elif 1 <= correct_answer <= len(q["options"]):
                                    correct_answer = q["options"][correct_answer - 1]

                            if str(answer).strip().lower() == str(correct_answer).strip().lower():
                                score += 1

                        st.session_state.score = score
                        st.session_state.submitted = True

                    if st.session_state.submitted:
                        st.html(f"""
                        <div style="
                            background:#eef7f1;
                            color:#23613b;
                            border:1px solid #cde8d7;
                            border-radius:12px;
                            padding:14px 18px;
                            margin-top:18px;
                            font-size:15px;
                            font-weight:600;
                        ">
                            Score: {st.session_state.score}/{len(quiz)}
                        </div>
                        """)
        else:
            st.error("Could not extract text from this PDF.")


# ---------------------------------------------------------
# SEARCH NOVELS
# ---------------------------------------------------------

elif page == "Search Novels":

    st.html("""
    <div class="page-title">Search Novels</div>
    <div class="page-subtitle">
        Find books by title, author, genre, or topic.
    </div>
    """)

    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input(
            "Novel Search",
            value=st.session_state.get("novel_search", ""),
            placeholder="Search for a novel, author, or topic...",
            label_visibility="collapsed"
        )
    with col2:
        search = st.button("Search", use_container_width=True)

    if search and query.strip():
        st.session_state["novel_search"] = query.strip()

    active_query = st.session_state.get("novel_search", "")

    if active_query:
        st.html(f"""
        <div style="font-size:15px;font-weight:700;color:#27365d;margin-bottom:6px;">
            Results for "{html.escape(active_query)}"
        </div>
        """)

        tab_free, tab_all = st.tabs(["📖 Read free (full books)", "🔎 All books (previews)"])

        with tab_free:
            st.caption("Public-domain classics from Project Gutenberg. Read them right here.")
            try:
                with st.spinner("Searching free books..."):
                    free_results = cached_search_free(active_query)
            except Exception as e:
                free_results = []
                st.error(f"Free book search failed: {e}")

            if free_results:
                render_book_grid(free_results, action_label="Save to Library",
                                 on_action=add_book, key_prefix="free")
            else:
                st.info("No free full-text edition found. Modern books are usually "
                        "copyrighted, so try the 'All books' tab for previews.")

        with tab_all:
            search_failed = False
            try:
                with st.spinner("Searching for books..."):
                    all_results = cached_search_all(active_query)
            except BookSearchError as e:
                all_results = []
                search_failed = True
                st.error(f"Book search failed: {e}")

            if all_results:
                render_book_grid(all_results, action_label="Save to Library",
                                 on_action=add_book, key_prefix="all")
            elif not search_failed:
                st.info("No results. Try a different title, author, or keyword.")
    else:
        st.html("""
        <div class="content-box">
            <div style="font-size:15px;font-weight:700;color:#27365d;margin-bottom:8px;">
                Discover your next book
            </div>
            <div style="font-size:11px;color:#8a96af;line-height:18px;">
                Search for novels, authors, genres and topics.
            </div>
        </div>
        """)


# ---------------------------------------------------------
# MOOD RECOMMENDATIONS
# ---------------------------------------------------------

elif page == "Mood Recommendations":

    st.html("""
    <div class="page-title">Mood Recommendations</div>
    <div class="page-subtitle">
        Tell ReadVerse how you're feeling and discover books that match your mood.
    </div>
    """)

    st.html("""
    <div class="content-box">
        <div style="
            font-size:15px;
            font-weight:700;
            color:#27365d;
            margin-bottom:14px;
        ">
            How are you feeling today?
        </div>
    </div>
    """)

    mood = st.selectbox(
        "Mood",
        [
            "Happy",
            "Calm",
            "Motivated",
            "Emotional",
            "Curious",
            "Romantic",
            "Looking for personal growth"
        ],
        label_visibility="collapsed"
    )

    find_clicked = st.button("Find Books")

    if find_clicked:
        st.session_state["mood_selected"] = mood

    active_mood = st.session_state.get("mood_selected")

    if active_mood:
        needs_fetch = (
            find_clicked
            or st.session_state.get("mood_results_for") != active_mood
        )

        if needs_fetch:
            with st.spinner(f"Finding books for your mood: {active_mood}..."):
                st.session_state["mood_results"] = search_books_by_mood(active_mood, max_results=12)
                st.session_state["mood_results_for"] = active_mood

        results = st.session_state.get("mood_results", [])

        if results:
            mood_html = html.escape(active_mood)
            st.html(f"""
            <div style="
                font-size:15px;
                font-weight:700;
                color:#27365d;
                margin:18px 0 14px 0;
            ">
                Books for when you're feeling {mood_html}
            </div>
            """)

            render_book_grid(results, action_label="Save to Library", on_action=add_book)
        else:
            st.html("""
            <div class="content-box">
                <div style="
                    font-size:15px;
                    font-weight:700;
                    color:#27365d;
                    margin-bottom:8px;
                ">
                    No matches found
                </div>
                <div style="font-size:11px;color:#8a96af;line-height:18px;">
                    Try selecting a different mood.
                </div>
            </div>
            """)


# ---------------------------------------------------------
# MY LIBRARY
# ---------------------------------------------------------

elif page == "My Library":

    st.html("""
    <div class="page-title">My Library</div>
    <div class="page-subtitle">
        Keep your favorite books and reading journey in one place.
    </div>
    """)

    library_books = load_library()

    if library_books:
        render_book_grid(
            library_books,
            action_label="Remove from Library",
            on_action=lambda book: remove_book(book.get("id"))
        )
    else:
        st.html("""
        <div class="content-box">
            <div style="
                text-align:center;
                padding:35px 20px;
            ">
                <div style="
                    font-size:28px;
                    font-weight:700;
                    color:#6478ff;
                    margin-bottom:10px;
                ">Library</div>

                <div style="
                    font-size:15px;
                    font-weight:700;
                    color:#27365d;
                    margin-bottom:7px;
                ">
                    Your library is empty
                </div>

                <div style="
                    font-size:11px;
                    color:#8b96ae;
                ">
                    Save your favorite books here and
                    build your personal reading collection.
                </div>
            </div>
        </div>
        """)