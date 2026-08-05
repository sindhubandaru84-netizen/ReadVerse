
from dotenv import load_dotenv
import os
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ask_question(text, question):

    prompt = f"""
    You are ReadVerse, an AI assistant that answers questions
    based only on the provided document.

    Document:
    {text}

    Question:
    {question}

    Instructions:
    - Answer only using information from the document.
    - If the answer is not available in the document, say:
      "I couldn't find the answer in the provided document."
    - Explain the answer clearly and simply.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content
