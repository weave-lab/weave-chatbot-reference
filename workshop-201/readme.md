# Getting started

## Preparation

- Python
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

```
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env # run this or start a new terminal
uv --version # test that uv is installed
```

- Ollama - Ollama is a tool for running LLMs locally
    - You can download Ollama from [here](https://ollama.com/download)
    - Copy Ollama.app to the `Applications` folder on MacOS
    - Double click `Ollama.app` to start the Ollama daemon
    - Make sure you have the model `llama3.2:3b` downloaded
        - `ollama pull llama3.2:3b
    - You can check you have the model with `ollama list | grep llama3.2:3b`
    - You will need to have Ollama running to run our agent

- Visual Studio Code (VSCode) - You can download VSCode from [here](https://code.visualstudio.com/Download)

## Running the Agent

```
cd ~/go/src/weavelab.xyz/weave-chatbot-reference/workshop-201 # you might need to change the start of this path
uv run python teachers_assistant.py
```

You should now be able to ask the teacher questions. Here are some sample prompts. The agent maintains history, so once
started you can hit `Up` or `Down` to cycle through previous prompts.

If a prompt doesn't actually get run, try hitting `Up` then `Enter` 

## Sample Prompts

Here are some sample prompts you can use to test the agent:

- What is the derivative of x^2 + 3x + 2?
- Translate 'Hello, how are you?' to Spanish
- Explain the concept of polymorphism in object-oriented programming
- What is the capital of France?
- Solve the quadratic equation x^2 + 5x + 6 = 0. Please give an explanation and translate it to German
- What is the date today?

## Running the eval notebook

- Open Visual Studio Code
- Open the `weave-chatbot-reference` folder
- Open the `workshop-201/llm_evals_teachers_assistant.ipynb` file
- Click `Select Kernel` in the top right of the notebook
- Click on `weave-chatbot-reference`
- Click on `Run All` to run all the cells in the notebook



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