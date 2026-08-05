

from extract import extract_text
from chunk import split_text
from embeddings import create_embeddings
from vector_store import create_index, search_index
from important import explain_topic


# Load PDF
pdf_text = extract_text("sample.pdf")

print("PDF loaded successfully!")


# Split PDF into chunks
chunks = split_text(pdf_text)

print("Number of chunks:", len(chunks))


# Create embeddings for PDF chunks
embeddings = create_embeddings(chunks)

print("Embeddings created!")


# Create FAISS index
index = create_index(embeddings)

print("FAISS index created!")


# Find relevant chunks
def retrieve_chunks(question, chunks, index):

    # Convert question into an embedding
    question_embedding = create_embeddings([question])

    # Search FAISS
    distances, indices = search_index(
        index,
        question_embedding,
        k=3
    )

    # Get the actual text of the relevant chunks
    relevant_chunks = []

    for i in indices[0]:
        relevant_chunks.append(chunks[i])

    return relevant_chunks


# Ask the user
question = input("\nAsk a question about the PDF: ")


# Retrieve relevant PDF chunks
relevant_chunks = retrieve_chunks(
    question,
    chunks,
    index
)


# Combine the retrieved chunks
context = "\n\n".join(relevant_chunks)


# Send retrieved information to Groq
answer = explain_topic(question,context)


# Display final answer
print("\nAnswer:\n")
print(answer)
