from google import genai
from google.genai import types
from pymilvus import MilvusClient  # type:ignore[import-untyped]
from chunking import MarkdownChunker


# This is a Milvus-based vector store showcasing optimized vector database performance benefits on latency.
# In production, Weave utilizes Elasticsearch for all vector store operations.
# For production implementation with Elasticsearch, refer to: https://github.com/weave-lab/search-api
# Please reach out to MLOps team for implementation guidance.
class MilvusVectorStore:
    """MilvusVectorStore provides optimized functionality for storing and retrieving text documents using semantic similarity search with Milvus Lite."""

    def __init__(
        self,
        vector_db_path: str,
        genai_client: genai.Client,
        embedding_model: str = "gemini-embedding-001",
        embedding_dimension: int = 768,
    ):
        """
        Initialize the Milvus vector store.

        Args:
            vector_db_path (str): Path to the Milvus database file.
            genai_client (genai.Client): The GenAI client for embedding generation.
            embedding_model (str, optional): The embedding model to use for generating document and query embeddings. Defaults to "gemini-embedding-001".
            embedding_dimension (int, optional): The dimension of the embeddings. Defaults to 768.
        """
        self.vector_db_path = vector_db_path
        self.genai_client = genai_client
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension

        # Initialize Milvus client
        self.milvus_client = MilvusClient(self.vector_db_path)

    def _generate_embedding(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> list[float]:
        """
        Generate embedding for a given text using the specified embedding model.

        Args:
            text (str): The text to generate an embedding for.
            task_type (str, optional): The task type for embedding generation.

        Note: For a list of supported task types, refer to: https://ai.google.dev/gemini-api/docs/embeddings#supported-task-types
        For embeddings optimized for general search queries, use RETRIEVAL_QUERY for queries; RETRIEVAL_DOCUMENT for documents to be retrieved.
        """
        response = self.genai_client.models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type, output_dimensionality=self.embedding_dimension
            ),  # Ensure embedding dimension matches Milvus collection dimension
            # gemini-embedding-001 supports dimensions up to 3072, that changes with model.
            # Please refer https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings
            # Reducing dimension can lead to loss of information but improves performance.
        )
        if not response.embeddings or not response.embeddings[0].values:
            raise ValueError("Failed to generate embedding.")
        return response.embeddings[0].values

    def _process_markdown_file(self, file_path: str):
        """Ingest data from a single markdown file using chunking."""
        with open(file_path, "r") as f:
            content = f.read()

        # Chunk the content
        chunker = MarkdownChunker()
        chunks = chunker.chunk_text(content)

        # Prepare data for insertion
        data = []
        for i, chunk in enumerate(chunks):
            embedding = self._generate_embedding(chunk, task_type="RETRIEVAL_DOCUMENT")
            data.append(
                {
                    "id": i,
                    "vector": embedding,
                    "text": chunk,
                }
            )
        return data

    def create_collection(self, doc_paths: list[str], collection_name: str):
        """Create a Milvus collection and ingest documents from the provided markdown file paths."""

        # Drop existing collection if it exists (for re-ingestion scenarios)
        if self.milvus_client.has_collection(collection_name=collection_name):
            self.milvus_client.drop_collection(collection_name=collection_name)

        self.milvus_client.create_collection(
            collection_name=collection_name,
            dimension=self.embedding_dimension,
        )

        for doc_path in doc_paths:
            data = self._process_markdown_file(doc_path)
            # Insert data into collection
            if data:
                self.milvus_client.insert(collection_name=collection_name, data=data)

    def retrieve(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        verbose: bool = False,
    ) -> list:
        """Retrieve the top_k most similar documents using Milvus vector search."""
        # Generate embedding for the query string.
        query_embedding = self._generate_embedding(query, task_type="RETRIEVAL_QUERY")

        # Perform vector search using Milvus
        search_results = self.milvus_client.search(
            collection_name=collection_name,
            data=[query_embedding],
            limit=top_k,
            output_fields=["text"],
        )

        retrieved_context = [result["text"] for result in search_results[0]]
        if verbose:
            print("\n--- Retrieved Context Details ---", flush=True)
            for data in search_results[0]:
                for key, value in data.items():
                    print(f"{key}: {value}", flush=True)
            print("-------------------------------\n", flush=True)

        return retrieved_context
