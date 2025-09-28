# Workshop 101 - Retrieval-Augmented Generation

This workshop demonstrates how to build a chatbot using Retrieval-Augmented Generation (RAG).

## Features

- Retrieval-Augmented Generation (RAG) chatbot
- Vector database integration
- Natural language processing
- LLM-based evaluation system

## Running the Service

To run the chatbot:

```bash
uv run workshop-101/app.py
```

## Evaluation

To evaluate your RAG system's performance:

```bash
uv run workshop-101/eval_rag.py
```

### Test Cases

The `goldens.jsonl` file contains test cases, where each line should contain a JSON object representing a test case.

The evaluation measures:
- **Answer Quality**: How well the generated answers match the expected answers
- **Context Precision**: How well relevant information is ranked first in retrieval