# Weave Chatbot Reference

A Retrieval-Augmented Generation (RAG) chatbot demonstration built with Python.

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) package manager

## Setup

1. Clone the repository:
```bash
git clone 
cd rag-chatbot-demo
```

2. Install dependencies:
```bash
uv sync
```

## Usage

```bash
uv run app.py
```

## Project Structure

```
rag-chatbot-demo/
├── README.md
├── app.py
├── pyproject.toml
├── rag_utils.py
├── prompts/
├──── system_prompt_v1.txt
└──── system_prompt_v2.txt
```

## Features

- Retrieval-Augmented Generation chatbot
- Vector database integration
- Natural language processing

## Dependencies

Dependencies are managed through uv. See `requirements.txt` for the full list.