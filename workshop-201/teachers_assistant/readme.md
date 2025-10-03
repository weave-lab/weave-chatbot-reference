# Getting started

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
 
```
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env # run this or start a new terminal
uv --version # test that uv is installed
```

- Ollama - Ollama is a tool for running local LLMs
  - You can download Ollama from [here](https://ollama.com/download)
  - Please install Ollama locally
  - Please make sure that Ollama is running

## Running the Agent
```
uv venv --python=3.13.2
source .venv/bin/activate
uv sync
python teachers_assistant.py
```

## Files

This directory contains the implementation files for several agents and then a main orchestrator agent called
`teachers_assistant.py`. The `teachers_assistant` agent routes incoming prompts to one or more of the specialized
agents.

- [teachers_assistant.py](teachers_assistant.py) - The main orchestrator agent that routes queries to specialized agents
- [math_assistant.py](math_assistant.py) - Specialized agent for handling mathematical queries
- [language_assistant.py](language_assistant.py) - Specialized agent for language translation tasks
- [english_assistant.py](english_assistant.py) - Specialized agent for English grammar and comprehension
- [computer_science_assistant.py](computer_science_assistant.py) - Specialized agent for computer science and
  programming tasks
- [the_greatest_day_ive_ever_known.py](the_greatest_day_ive_ever_known.py) - Get the current day
- [no_expertise.py](no_expertise.py) - General assistant for queries outside specific domains

## Strands Agents Framework

This code is built on the agent framework [Strands](https://strandsagents.com/latest/) and based on their multi-agent
example, which is [here](multi_agent_example.md)

## Sample Prompts

Here are some sample prompts you can use to test the agent:
- What is the derivative of x^2 + 3x + 2?
- Translate 'Hello, how are you?' to Spanish
- Explain the concept of polymorphism in object-oriented programming
- What is the capital of France?
- Solve the quadratic equation x^2 + 5x + 6 = 0. Please give an explanation and translate it to German
- What is the date today?

## 