# Weave Chatbot Reference

A Retrieval-Augmented Generation (RAG) chatbot demonstration built with Python.

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) package manager

## Getting Started

1. Clone It
```bash
git clone https://github.com/weave-lab/weave-chatbot-reference.git
cd weave-chatbot-refence
```

2. Run It

```bash
uv run app.py
```

## Project Structure

```
weave-chatbot-refence/
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