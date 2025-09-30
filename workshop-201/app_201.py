import argparse  # Import argparse for command-line argument parsing
from pathlib import Path
from google import genai
from google.genai.types import GenerateContentConfig
from vector_store import MilvusVectorStore

# Define global constants for project and location
PROJECT_ID = "weave-ai-sandbox"
LOCATION = "us-central1"
VECTOR_TOP_K = 5  # Max number of top similar documents to retrieve


# Function to read versioned system prompt from a file, defaulting to "v1".
# This function assumes the prompt files are stored in a "prompts" directory relative to this script.
def read_prompt_from_file(version: str = "v1") -> str:
    """Read the system prompt from a file based on the specified version."""
    current_file = Path(__file__).parent
    file_path = current_file / "prompts" / f"system_prompt_{version}.txt"
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise ValueError(f"Prompt version '{version}' not found at {file_path}")


def generate_chat_response(
    client: genai.Client,
    system_prompt: str,
    user_message: str,
    chat_history: list = [],
    context_snippets: list = [],
    model: str = "gemini-2.5-flash",
    verbose: bool = False,
) -> str:
    """Generate a chat response using the GenAI client with optional RAG context."""
    config = GenerateContentConfig(
        temperature=0.2,  # Lower temperature for more deterministic responses; this roughly corresponds to "creativity" in the model
        max_output_tokens=512,  # Limit the response length to 512 tokens
        # top_p=0.95,  # Top-p sampling for diversity; this is a common setting for chat models
        # top_k=40,  # Top-k sampling to limit the number of tokens considered
        system_instruction=system_prompt,  # System prompt to set the context for the chat model; Google only allows this in client initialization
    )

    context_text = "\n\n".join(context_snippets)

    # Supports the roles "user" and "model"
    messages = chat_history.copy()  # Enrich with past context here...
    if context_text:
        # This structure is mandated by Google's interface; it is not a general standard.
        messages.append(
            {"role": "model", "parts": [{"text": f"Relevant context:\n{context_text}"}]}
        )

    chat_session = client.chats.create(
        model=model,
        config=config,
        history=messages,
    )

    if verbose:
        print("\n--- Chat Session History ---", flush=True)
        print(chat_session.get_history(), flush=True)
        print("--------------------------\n", flush=True)

    response = chat_session.send_message(user_message)
    if not response or not response.text:
        raise ValueError("Failed to generate chat response.")

    return response.text


from pathlib import Path

def init_vector_store(
    client: genai.Client, collection_name: str = "weave_docs", reingest: bool = False
) -> MilvusVectorStore:
    """Initialize the Milvus vector store and ingest documents if needed."""
    current_file = Path(__file__).parent
    doc_paths = [str(current_file / "data" / "waml.md")]
    vector_db_path = current_file / "vector_db" / "milvus.db"
    # Ensure the parent directory exists
    vector_db_path.parent.mkdir(parents=True, exist_ok=True)
    # Initialize Milvus vector store
    vector_store = MilvusVectorStore(vector_db_path=str(vector_db_path), genai_client=client)
    # Create collection if it doesn't exist or if reingestion is forced
    if reingest or not vector_store.milvus_client.has_collection(collection_name):
        vector_store.create_collection(doc_paths, collection_name=collection_name)
    return vector_store


def main():
    """Main function to run the CLI chat client with RAG."""
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="CLI Chat Client with RAG using Milvus vector store."
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output for RAG retrieval details.",
    )
    parser.add_argument(
        "--collection",
        "-c",
        type=str,
        default="weave_docs",
        help="Name of the Milvus collection to use (default: weave_docs).",
    )
    parser.add_argument(
        "--reingest",
        "-r",
        action="store_true",
        help="Force re-ingestion of documents even if collection exists.",
    )
    args = parser.parse_args()

    # Initialize GenAI Client once
    genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    # Initialize vector store with new parameters
    print(f"Initializing Milvus vector store with collection '{args.collection}'...")
    if args.reingest:
        print("Force re-ingestion enabled - will recreate collection.")
    vector_store = init_vector_store(
        genai_client, collection_name=args.collection, reingest=args.reingest
    )
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

        # Retrieve relevant context, passing the verbose flag
        retrieved_context = vector_store.retrieve(
            query=user_message,
            collection_name=args.collection,
            top_k=VECTOR_TOP_K,
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
        # Append user message and response to chat history.
        # This is important for maintaining conversational context in the chat session.
        # The chat history structure is designed to be compatible with Google's chat interface.
        chat_history.append({"role": "user", "parts": [{"text": user_message}]})
        chat_history.append({"role": "model", "parts": [{"text": f"{response}"}]})
        print(f"Bot: {response}")


if __name__ == "__main__":
    main()
