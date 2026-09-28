from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)


def explain_topic(question, context):

    prompt = f"""
You are ReadVerse, an AI assistant that answers questions about uploaded PDFs.

Use ONLY the information given in the PDF context.

PDF CONTEXT:
{context}

USER QUESTION:
{question}

Instructions:
- Answer the question directly.
- Use only information from the PDF.
- Do not invent information.
- Do not give unrelated information.
- If the answer is present, answer it.
- If it is absent, say:
"I couldn't find that information in the PDF."

Answer:
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


def explain_pdf(context):

    prompt = f"""
You are ReadVerse, an AI learning assistant.

Explain the following PDF content in simple and understandable language.

PDF CONTENT:
{context}

Instructions:
- Explain the important information.
- Use simple language suitable for a beginner.
- Organize the explanation using headings.
- Use bullet points where useful.
- Explain difficult technical terms simply.
- Do not invent information.
- Do not include unrelated information.

Simple Explanation:
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


def generate_mcqs(context, num_questions=5, exclude_questions=None):

    exclude_block = ""
    if exclude_questions:
        already_used = "\n".join(f"- {q}" for q in exclude_questions)
        exclude_block = f"""
These questions have already been used. Do NOT repeat them or create
close variations of them:
{already_used}
"""

    prompt = f"""
You are ReadVerse, an AI quiz generator.

Create exactly {num_questions} multiple-choice questions from the PDF content.

PDF CONTENT:
{context}
{exclude_block}
Rules:
- Use ONLY information from the PDF.
- Each question must have exactly 4 options.
- Each question must have one correct answer.
- Do NOT include explanations.
- Do NOT include the correct answer outside the JSON.
- Return ONLY valid JSON.
- Do not use markdown.

Return exactly this format:

[
  {{
    "question": "Question text",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": 0
  }}
]

The answer field must be:
0 for Option A
1 for Option B
2 for Option C
3 for Option D
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    return response.choices[0].message.content