from google import genai
from sklearn.metrics.pairwise import cosine_similarity  # type:ignore[import-untyped]
import numpy as np
from typing import NamedTuple


class Document(NamedTuple):
    text: str
    embedding: np.ndarray


# This is a simple in-memory vector store for demonstration purposes.
# In a production system, you would likely use a more robust solution like Matching Engine, FAISS, etc.
# MLOps will provide a more scalable and efficient vector store solution.
class InMemoryVectorStore:
    def __init__(self):
        self.documents: list[Document] = []

    def add_document(self, text: str, embedding: np.ndarray):
        # Add a document with its text and embedding to the vector store.
        # Embeddings are a numerical representation of the text,
        # they are somewhat like a fingerprint of the text, allowing for similarity comparisons.
        self.documents.append(Document(text=text, embedding=embedding))

    def retrieve(
        self,
        query_embedding: np.ndarray,
        top_k: int = 3,
        similarity_threshold: float = 0.7,
        verbose: bool = False,
    ) -> list:
        # Retrieve the top_k most similar documents based on cosine similarity.
        # Cosine similarity measures the cosine of the angle between two vectors.
        # A higher cosine similarity indicates that the vectors are more similar.
        # For simplicity, we take the first embedding, in reality you may have multiple embeddings
        # requiring a more complex handling.
        similarities = []
        for doc in self.documents:  # Iterate over Document objects
            # Calculate cosine similarity between the query and document embeddings.
            # The reshape is necessary to ensure the dimensions match for cosine similarity calculation.
            # This will return a single similarity score for each document which can be used to rank the documents.
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1), doc.embedding.reshape(1, -1)
            )[0][0]
            similarities.append((similarity, doc.text))  # Store text from Document

        # Sort the documents by similarity score in descending order to make taking the top_k most similar documents easier.
        similarities.sort(key=lambda x: x[0], reverse=True)

        if verbose:
            print("\n--- Retrieved Context Details ---", flush=True)
            for sim, text in similarities[:top_k]:
                print(f"Similarity: {sim:.4f}, Text: '{text}'", flush=True)
            print("-------------------------------\n", flush=True)

        return [
            text for sim, text in similarities[:top_k] if sim > similarity_threshold
        ]


def get_embedding(
    text: str, vertext_client: genai.Client, model_name: str = "gemini-embedding-001"
) -> np.ndarray:
    # Use genai.embed_content for generating embeddings
    # The project and location are configured globally or handled by the environment
    # Embeddings are a numerical representation of the text,
    # they are somewhat like a fingerprint of the text, allowing for similarity comparisons.
    response = vertext_client.models.embed_content(model=model_name, contents=text)
    if not response.embeddings or not response.embeddings[0].values:
        raise ValueError("Failed to generate embedding.")
    return np.array(response.embeddings[0].values)
