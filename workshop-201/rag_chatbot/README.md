# Workshop 201 - Advanced RAG with Evaluation

This workshop demonstrates advanced RAG techniques using vector databases, chunking strategy and evaluation using a framework

## Features

- **Vector Database**: Milvus vector store with persistent storage
- **Advanced Chunking**: Markdown chunking strategies
- **Comprehensive Evaluation**: LLM-based evaluation using Ragas framework

## Running the Service

To run the advanced RAG chatbot:

```bash
uv run workshop-201/rag_chatbot/app_201.py
```

### Command Line Options

- `--verbose`, `-v`: Enable verbose output for RAG retrieval details
- `--collection`, `-c`: Specify Milvus collection name (default: weave_docs)
- `--reingest`, `-r`: Force re-ingestion of documents

### Interactive Commands

During chat:
- `verbose`: Toggle verbose mode on/off
- `history`: View conversation history
- `quit` or `exit`: End the chat session

## Evaluation

### Jupyter Notebook Evaluation

Open and run the comprehensive evaluation notebook:

```bash
jupyter lab workshop-201/rag_chatbot/llm_evals.ipynb
```