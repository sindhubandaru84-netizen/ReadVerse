
from sentence_transformers import SentenceTransformer


model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(chunks):

    embeddings = model.encode(chunks)

    return embeddings


if __name__ == "__main__":

    test_chunks = [
        "Java is a programming language.",
        "Python is used for machine learning.",
        "Electrical engineering deals with electrical systems."
    ]

    embeddings = create_embeddings(test_chunks)

    print("Number of chunks:", len(embeddings))
    print("Embedding size:", len(embeddings[0]))
