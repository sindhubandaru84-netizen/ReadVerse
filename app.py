import streamlit as st
import json

from extract import extract_text
from chunk import split_text
from embeddings import create_embeddings
from vector_store import create_index, search_index
from important import explain_topic, explain_pdf, generate_mcqs


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="ReadVerse",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.html("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
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
    background: white;
    border: 1px solid #edf0f7;
    border-radius: 28px;
    box-shadow: 0 5px 18px rgba(67, 89, 145, 0.08);
    height: 42px;
}

div[data-testid="stTextInput"] input {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    font-size: 11px !important;
    color: #52617e !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #a2abc0 !important;
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
            <div class="logo-icon">📖</div>

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
            "🏠  Home",
            "📄  Upload & Read",
            "🔍  Search Novels",
            "😊  Mood Recommendations",
            "🔖  My Library"
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

if page == "🏠  Home":

    # Hero
    st.html("""
    <div class="hero">

        <div class="welcome">
            WELCOME TO
        </div>

        <div class="hero-title">
            Read<span>Verse</span>
        </div>

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

        <div class="hero-cup">
            ☕
        </div>

        <div class="hero-plant">
            🌿
        </div>

    </div>
    """)


    # Search
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

        search_clicked = st.button(
            "Search",
            use_container_width=True
        )

    if search_clicked and search_text.strip():
        st.session_state["novel_search"] = search_text.strip()
        st.session_state["go_to_search"] = True
        st.rerun()


    # Feature cards
    st.html("""
    <div style="height:2px"></div>

    <div style="
        display:grid;
        grid-template-columns:repeat(4,1fr);
        gap:14px;
    ">

        <div class="feature-card feature-purple">

            <div class="feature-icon icon-purple">
                📖
            </div>

            <div class="feature-title">
                Upload & Read
            </div>

            <div class="feature-text">
                Upload your PDF and get
                instant summaries, explanations
                and key insights.
            </div>

            <div class="feature-arrow">
                →
            </div>

        </div>


        <div class="feature-card feature-green">

            <div class="feature-icon icon-green">
                🔍
            </div>

            <div class="feature-title">
                Search Novels
            </div>

            <div class="feature-text">
                Find your next favorite book
                by searching titles, authors
                or genres.
            </div>

            <div class="feature-arrow">
                →
            </div>

        </div>


        <div class="feature-card feature-pink">

            <div class="feature-icon icon-pink">
                😊
            </div>

            <div class="feature-title">
                Mood Recommendations
            </div>

            <div class="feature-text">
                Tell us how you feel, and get
                personalized book suggestions
                just for you.
            </div>

            <div class="feature-arrow">
                →
            </div>

        </div>


        <div class="feature-card feature-blue">

            <div class="feature-icon icon-blue">
                🔖
            </div>

            <div class="feature-title">
                My Library
            </div>

            <div class="feature-text">
                Save your favorite books
                and keep track of your
                reading journey.
            </div>

            <div class="feature-arrow">
                →
            </div>

        </div>

    </div>
    """)


    # Popular books heading
    st.html("""
    <div class="section-heading">

        <div class="section-title">
            <span>✦</span>
            Popular Books
        </div>

        <div class="view-all">
            View all →
        </div>

    </div>
    """)


    # Books
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

                <div class="book-cover {cover}">
                    {title}
                </div>

                <div class="book-title">
                    {title}
                </div>

                <div class="book-author">
                    {author}
                </div>

                <div class="book-tag">
                    {tag}
                </div>

            </div>
            """)


# ---------------------------------------------------------
# UPLOAD & READ
# ---------------------------------------------------------

elif page == "📄  Upload & Read":

    st.html("""
    <div class="page-title">
        Upload & Read
    </div>

    <div class="page-subtitle">
        Upload a PDF and explore its content with ReadVerse.
    </div>
    """)

    uploaded_file = st.file_uploader(
        "Upload your PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        with open("uploaded.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("PDF uploaded successfully!")

        text = extract_text("uploaded.pdf")

        if text:

            chunks = split_text(text)
            embeddings = create_embeddings(chunks)
            index = create_index(embeddings)

            st.session_state["chunks"] = chunks
            st.session_state["index"] = index

            st.html("""
            <div class="content-box">
            """)
            
            option = st.radio(
                "Choose an option",
                [
                    "🧠 Explain PDF",
                    "❓ Ask a Question",
                    "📝 Generate MCQs"
                ]
            )

            st.html("""
            </div>
            """)

            # -------------------------------------------------
            # EXPLAIN PDF
            # -------------------------------------------------

            if option == "🧠 Explain PDF":

                if st.button("Explain PDF"):

                    with st.spinner("Reading and explaining your PDF..."):

                        explanation = explain_pdf(text)

                    st.subheader("📖 Explanation")
                    st.write(explanation)


            # -------------------------------------------------
            # ASK QUESTION
            # -------------------------------------------------

            elif option == "❓ Ask a Question":

                question = st.text_input(
                    "Enter your question",
                    placeholder="Ask something about the PDF..."
                )

                if st.button("Ask Question") and question:

                    query_embedding = create_embeddings([question])

                    results = search_index(
                        index,
                        query_embedding,
                        chunks
                    )

                    context = "\n".join(results)

                    answer = explain_topic(
                        context,
                        question
                    )

                    st.subheader("💡 Answer")
                    st.write(answer)


            # -------------------------------------------------
            # GENERATE MCQS
            # -------------------------------------------------

            elif option == "📝 Generate MCQs":

                if "quiz" not in st.session_state:
                    st.session_state.quiz = None

                if "submitted" not in st.session_state:
                    st.session_state.submitted = False

                if "score" not in st.session_state:
                    st.session_state.score = 0

                if st.button("Generate MCQs"):

                    with st.spinner("Generating questions..."):

                        quiz_data = generate_mcqs(text)

                    try:
                        if isinstance(quiz_data, str):
                            quiz_data = json.loads(quiz_data)

                        st.session_state.quiz = quiz_data
                        st.session_state.submitted = False
                        st.session_state.score = 0

                    except Exception:

                        st.error(
                            "Could not read the generated quiz. "
                            "Please try again."
                        )

                if st.session_state.quiz:

                    quiz = st.session_state.quiz

                    st.subheader("📝 Quiz")

                    for i, q in enumerate(quiz):

                        st.write(
                            f"**{i + 1}. {q['question']}**"
                        )

                        st.radio(
                            "Choose your answer",
                            q["options"],
                            key=f"question_{i}"
                        )

                    if st.button("Submit Quiz"):

                        score = 0

                        for i, q in enumerate(quiz):

                            answer = st.session_state.get(
                                f"question_{i}"
                            )

                            if answer == q["answer"]:
                                score += 1

                        st.session_state.score = score
                        st.session_state.submitted = True

                        st.rerun()

                    if st.session_state.submitted:

                        st.success(
                            f"Your score: "
                            f"{st.session_state.score}/{len(quiz)}"
                        )


# ---------------------------------------------------------
# SEARCH NOVELS
# ---------------------------------------------------------

elif page == "🔍  Search Novels":

    st.html("""
    <div class="page-title">
        Search Novels
    </div>

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

        search = st.button(
            "Search",
            use_container_width=True
        )

    if search and query:

        st.session_state["novel_search"] = query

        st.html(f"""
        <div class="content-box">

            <div style="
                font-size:14px;
                font-weight:700;
                color:#27365d;
                margin-bottom:8px;
            ">
                Search results for "{query}"
            </div>

            <div style="
                font-size:11px;
                color:#8a96af;
            ">
                🔎 Google Books search will be connected here.
            </div>

        </div>
        """)

    else:

        st.html("""
        <div class="content-box">

            <div style="
                font-size:14px;
                font-weight:700;
                color:#27365d;
                margin-bottom:8px;
            ">
                🔎 Discover your next book
            </div>

            <div style="
                font-size:11px;
                color:#8a96af;
                line-height:18px;
            ">
                Search for novels, authors, genres and topics.
                Google Books API integration can be added here.
            </div>

        </div>
        """)


# ---------------------------------------------------------
# MOOD RECOMMENDATIONS
# ---------------------------------------------------------

elif page == "😊  Mood Recommendations":

    st.html("""
    <div class="page-title">
        Mood Recommendations
    </div>

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
            "😊 Happy",
            "😌 Calm",
            "💪 Motivated",
            "😔 Emotional",
            "🧠 Curious",
            "❤️ Romantic",
            "🌱 Looking for personal growth"
        ],
        label_visibility="collapsed"
    )

    if st.button("Find Books"):

        st.success(
            f"Finding books for your mood: {mood}"
        )

        st.info(
            "AI-based mood recommendation will be connected here."
        )


# ---------------------------------------------------------
# MY LIBRARY
# ---------------------------------------------------------

elif page == "🔖  My Library":

    st.html("""
    <div class="page-title">
        My Library
    </div>

    <div class="page-subtitle">
        Keep your favorite books and reading journey in one place.
    </div>

    <div class="content-box">

        <div style="
            text-align:center;
            padding:35px 20px;
        ">

            <div style="
                font-size:38px;
                margin-bottom:10px;
            ">
                🔖
            </div>

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