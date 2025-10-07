## Overview

This workshop shows how to build a multi-agent AI system. The system consists of a main teacher's assistant and several
specialized agents that can handle different types of queries, such as math, language translation, English
grammar, and computer science. The teacher assistant agent routes incoming prompts to the appropriate specialized agent.
This document will help you get your environment up and running locally.

We will also get a Jupyter notebook running that evaluates the performance of the teacher's assistant using a set of
predefined prompts.

For the assignment you will add your own tool and agent to the system and then test it using the notebook. Good luck!

## Preparation

- Clone this repo

```bash
git clone https://github.com/weave-lab/weave-chatbot-reference.git
cd weave-chatbot-reference
````

- Python
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env # run this or start a new terminal
uv --version # test that uv is installed
```

- Ollama - Ollama is a tool for running LLMs locally
- Even if you have Ollama already installed, make sure you install 3.2
    - You can download Ollama from [here](https://ollama.com/download)
    - Copy Ollama.app to the `Applications` folder on MacOS
    - Double click `Ollama.app` to start the Ollama daemon
    - Make sure you have the model `llama3.2:3b` downloaded. 3.2 is the version of the model, not the Ollama app itself
        - `ollama pull llama3.2:3b`
    - You can check you have the model with `ollama list | grep llama3.2:3b`
    - You will need to have Ollama running to run our agent

- Visual Studio Code (VSCode) - You can download VSCode from [here](https://code.visualstudio.com/Download)
    - Update VSCode as needed
    - Install the Python extension as needed
    - Install the Jupyter extension as needed
    - Update plugins as needed
    - If you do much, probably a good idea to restart VSCode

## Running the Agent

```bash
uv run workshop-201/teachers_assistant.py
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
- Open the `weave-chatbot-reference` folder. Please note that this is the parent folder of the repo. Opening the
  workshop-201 folder directly will not work correctly
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

## Assignment

- Improve any tests as you see fit!
- Add a tool that does something useful or at least does something :)
- Add evaluations for your new tool using the notebook

## Getting help

Please post to `#mlops` on Slack if you could use some help getting started!