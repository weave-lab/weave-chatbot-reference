## Getting started

```
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python teachers_assistant.py
```

This directory contains the implementation files for several agents and then a main orchestrator agent called `teachers_assistant.py`. The `teachers_assistant` agent routes incoming prompts to one or more of the specialized agents.

## Implementation Files

- [teachers_assistant.py](teachers_assistant.py) - The main orchestrator agent that routes queries to specialized agents
- [math_assistant.py](math_assistant.py) - Specialized agent for handling mathematical queries
- [language_assistant.py](language_assistant.py) - Specialized agent for language translation tasks
- [english_assistant.py](english_assistant.py) - Specialized agent for English grammar and comprehension
- [computer_science_assistant.py](computer_science_assistant.py) - Specialized agent for computer science and programming tasks
- [no_expertise.py](no_expertise.py) - General assistant for queries outside specific domains

## Documentation

This code is built on the agent framework [Strands](https://strandsagents.com/latest/) and based on their multi-agent example, which is [here](multi_agent_example.md).