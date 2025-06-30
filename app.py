import os
import argparse  # Import argparse for command-line argument parsing
from google import genai
from rag_utils import InMemoryVectorStore, get_embeddings

# Define global constants for project and location
PROJECT_ID = "weave-ai-sandbox"
LOCATION = "us-central1"
SIMILARITY_THRESHOLD = 0.75  # Threshold for similarity in RAG retrieval
VECTOR_TOP_K = 3  # Max number of top similar documents to retrieve


# Function to read versioned system prompt from a file, defaulting to "v1"
# This function assumes the prompt files are stored in a "prompts" directory.
def read_prompt_from_file(version: str = "v1") -> str:
    file_path = os.path.join("prompts", f"system_prompt_{version}.txt")
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise ValueError(f"Prompt version '{version}' not found at {file_path}")


# Function to chunk text into smaller pieces
# This is a simplified version; in practice, you might want to use more sophisticated chunking
# strategies to ensure meaningful context is preserved.
# For example, you might want to split by sentences or paragraphs rather than fixed character counts.
# This is especially important for RAG applications where context matters.
def chunk_text(text: str, chunk_size=512, overlap=50) -> list:
    # Overly simplified chunking
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def generate_chat_response(
    client: genai.Client,
    system_prompt: str,
    user_message: str,
    chat_history: list = [],
    context_snippets: list = [],
    model: str = "gemini-2.5-flash",
    verbose: bool = False,
) -> str:
    parameters = {
        "temperature": 0.2,  # Lower temperature for more deterministic responses, this roughly corresponds to "creativity" in the model
        "max_output_tokens": 512,  # Limit the response length to 512 tokens
        # "top_p": 0.95, # Top-p sampling for diversity, this is a common setting for chat models
        # "top_k": 40, # Top-k sampling to limit the number of tokens considered
        "system_instruction": system_prompt,  # System prompt to set the context for the chat model, Google only allowes this in client initialization
    }
    context_text = "\n\n".join(context_snippets)

    # Supports the roles "user" and "model"
    messages = chat_history.copy()  # Enrich with past context here...
    if context_text:
        # This structure is mandated by Google's interface, it is not a general standard.
        messages.append(
            {"role": "model", "parts": [{"text": f"Relevant context:\n{context_text}"}]}
        )

    chat_session = client.chats.create(
        model=model,
        config=parameters,
        history=messages,
    )

    if verbose:
        print("\n--- Chat Session History ---", flush=True)
        print(chat_session.get_history(), flush=True)
        print("--------------------------\n", flush=True)

    response = chat_session.send_message(user_message)

    return response.text


def init_vector_store(client: genai.Client) -> InMemoryVectorStore:
    # Sample documents for RAG
    documents = [
        "The capital of Utah is Salt Lake City.",
        "Salt Lake City is known for its proximity to the Great Salt Lake.",
        "The first governor of Utah was Blue Bayou.",  # This is a fictional example, to show knowledge retrieval can supplant the base model's knowledge
        "Brigham Young was a leader in the Latter-day Saint movement.",
        "The current governor of Utah is Spencer Cox.",
        "Utah is a state in the Western United States.",
    ]

    # Initialize vector store
    vector_store = InMemoryVectorStore()

    # Chunk documents and add to vector store
    for doc in documents:
        chunks = chunk_text(doc)  # Using the existing chunk_text function
        for chunk in chunks:
            embeddings = get_embeddings(chunk, client)
            for embedding in embeddings:
                vector_store.add_document(chunk, embedding)

    return vector_store


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="CLI Chat Client with RAG.")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output for RAG retrieval details.",
    )
    args = parser.parse_args()

    # Initialize GenAI Client once
    genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    # Initialize vector store
    vector_store = init_vector_store(genai_client)
    system_prompt = read_prompt_from_file()
    chat_history = []  # To store past messages for conversational context

    print(
        "CLI Chat Client. Type 'quit' or 'exit' to end the chat.\n"
        "Type 'verbose' to toggle verbose mode, and 'history' to view chat history.\n"
    )
    while True:  # REPL for CLI chat
        user_message = input("You: ")
        if user_message.lower().strip() == "verbose":
            args.verbose = not args.verbose
            print(f"Verbose mode {'enabled' if args.verbose else 'disabled'}.")
            continue
        elif user_message.lower().strip() == "history":
            print("\n--- Chat History ---")
            for entry in chat_history:
                role = entry["role"]
                text = "".join(part["text"] for part in entry["parts"])
                print(f"{role.capitalize()}: {text}")
            print("--------------------\n")
            continue
        elif user_message.lower().strip() in ["quit", "exit"]:
            break

        # Get embedding for user query
        query_embedding = get_embeddings(user_message, genai_client)

        # Retrieve relevant context, passing the verbose flag
        retrieved_context = vector_store.retrieve(
            query_embedding,
            top_k=VECTOR_TOP_K,
            similarity_threshold=SIMILARITY_THRESHOLD,
            verbose=args.verbose,
        )

        # Generate chat response
        # The generate_chat_response function already handles history structure and context snippets for Gemini
        response = generate_chat_response(
            genai_client,
            system_prompt,
            user_message,
            chat_history,
            retrieved_context,
            verbose=args.verbose,
        )
        # Append user message and response to chat history
        # This is important for maintaining conversational context in the chat session.
        # The chat history structure is designed to be compatible with Google's chat interface.
        chat_history.append({"role": "user", "parts": [{"text": user_message}]})
        chat_history.append({"role": "model", "parts": [{"text": f"{response}"}]})
        print(f"Bot: {response}")


if __name__ == "__main__":
    main()
