import streamlit as st
import json

from extract import extract_text
from chunk import split_text
from embeddings import create_embeddings
from vector_store import create_index, search_index
from important import explain_topic, explain_pdf, generate_mcqs


st.set_page_config(
    page_title="ReadVerse",
    page_icon="📚",
    layout="wide"
)

st.title("📚 ReadVerse")
st.write("Learn, understand, and practice from your PDF")


uploaded_file = st.file_uploader(
    "Upload your PDF",
    type=["pdf"],
    key="pdf_uploader"
)


if uploaded_file is not None:

    with open("uploaded.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    pdf_text = extract_text("uploaded.pdf")

    chunks = split_text(pdf_text)

    if len(chunks) == 0:
        st.error("Could not extract readable text from this PDF.")
        st.stop()

    embeddings = create_embeddings(chunks)

    index = create_index(embeddings)

    st.success("✅ PDF is ready!")

    option = st.radio(
        "What would you like to do?",
        [
            "🧠 Explain PDF",
            "❓ Ask a Question",
            "📝 Generate MCQs"
        ],
        horizontal=True,
        key="feature_selection"
    )


    # ==========================================
    # EXPLAIN PDF
    # ==========================================

    if option == "🧠 Explain PDF":

        if st.button("🧠 Explain PDF", key="explain_button"):

            with st.spinner("Reading and explaining your PDF..."):

                context = "\n\n".join(chunks)

                explanation = explain_pdf(context)

            st.subheader("🧠 Simple Explanation")

            st.write(explanation)


    # ==========================================
    # ASK QUESTION
    # ==========================================

    elif option == "❓ Ask a Question":

        question = st.text_input(
            "What would you like to know?",
            key="question_input"
        )

        if question:

            with st.spinner("Searching the PDF..."):

                question_embedding = create_embeddings(
                    [question]
                )

                distances, indices = search_index(
                    index,
                    question_embedding,
                    k=min(4, len(chunks))
                )

                relevant_chunks = []

                for i in indices[0]:
                    relevant_chunks.append(chunks[i])

                context = "\n\n".join(relevant_chunks)

                answer = explain_topic(
                    question,
                    context
                )

            st.subheader("💡 Answer")

            st.write(answer)


    # ==========================================
    # MCQ QUIZ
    # ==========================================

    elif option == "📝 Generate MCQs":

        if "quiz" not in st.session_state:
            st.session_state.quiz = None

        if "submitted" not in st.session_state:
            st.session_state.submitted = False

        if "score" not in st.session_state:
            st.session_state.score = 0


        # ======================================
        # START / NEW QUIZ
        # ======================================

        button_text = (
            "📝 Start Quiz"
            if st.session_state.quiz is None
            else "🔄 New Quiz"
        )

        if st.button(button_text, key="quiz_button"):

            with st.spinner("Creating a new quiz..."):

                context = "\n\n".join(chunks)

                mcq_text = generate_mcqs(context)

                try:

                    quiz = json.loads(mcq_text)

                    st.session_state.quiz = quiz

                    st.session_state.submitted = False

                    st.session_state.score = 0

                    # Clear previous answers
                    for key in list(st.session_state.keys()):

                        if key.startswith("question_"):

                            del st.session_state[key]

                    st.rerun()

                except json.JSONDecodeError:

                    st.error(
                        "Could not create the quiz. Please try again."
                    )


        # ======================================
        # DISPLAY QUIZ
        # ======================================

        if st.session_state.quiz:

            st.subheader("📝 ReadVerse Quiz")

            answers = []

            for i, question in enumerate(
                st.session_state.quiz
            ):

                st.write(
                    f"### Question {i + 1}"
                )

                selected = st.radio(
                    question["question"],
                    question["options"],
                    index=None,
                    key=f"question_{i}"
                )

                answers.append(selected)


            # ==================================
            # SUBMIT
            # ==================================

            if not st.session_state.submitted:

                if st.button(
                    "✅ Submit Quiz",
                    key="submit_quiz"
                ):

                    if any(
                        answer is None
                        for answer in answers
                    ):

                        st.warning(
                            "⚠️ Please answer all questions before submitting."
                        )

                    else:

                        score = 0

                        for i, question in enumerate(
                            st.session_state.quiz
                        ):

                            correct_option = question[
                                "options"
                            ][
                                question["answer"]
                            ]

                            if answers[i] == correct_option:

                                score += 1

                        st.session_state.score = score

                        st.session_state.submitted = True

                        st.rerun()


            # ==================================
            # RESULTS
            # ==================================

            if st.session_state.submitted:

                total = len(
                    st.session_state.quiz
                )

                score = st.session_state.score

                st.success(
                    f"🎉 Your Score: {score} / {total}"
                )

                st.subheader("📊 Results")

                for i, question in enumerate(
                    st.session_state.quiz
                ):

                    correct_option = question[
                        "options"
                    ][
                        question["answer"]
                    ]

                    user_answer = st.session_state.get(
                        f"question_{i}"
                    )

                    st.write(
                        f"**Question {i + 1}:** "
                        f"{question['question']}"
                    )

                    if user_answer == correct_option:

                        st.success(
                            f"✅ Your answer: {user_answer}"
                        )

                    else:

                        st.error(
                            f"❌ Your answer: {user_answer}"
                        )

                        st.info(
                            f"✅ Correct answer: "
                            f"{correct_option}"
                        )