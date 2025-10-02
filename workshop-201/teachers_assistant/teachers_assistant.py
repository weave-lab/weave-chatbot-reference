#!/usr/bin/env python3
"""
# 📁 Teacher's Assistant Strands Agent

A specialized Strands agent that orchestrates sub-agents to answer user queries.
This module can be used both as a command-line tool and as a library.
"""
from strands import Agent
from math_assistant import math_assistant
from english_assistant import english_assistant
from language_assistant import language_assistant
from computer_science_assistant import computer_science_assistant
from no_expertise import general_assistant
from strands.models.ollama import OllamaModel
from the_greatest_day_ive_ever_known import today
import readline
import os
import re
import argparse
from rich.console import Console
from rich.markdown import Markdown
import json
from typing import Optional, Dict, Any

TEACHER_SYSTEM_PROMPT = """
For any query, autonomously plan and execute all necessary tool calls in sequence to fully resolve the user's request. Chain outputs between tools as needed, and return the final result. Do not ask the user to perform intermediate steps or confirm actions; handle everything automatically.

Only call the Language Agent if the user explicitly requests a translation or a response in another language. Do not translate or call the Language Agent unless asked.

You are TeachAssist, a sophisticated educational orchestrator designed to coordinate educational support across multiple subjects. Your role is to:

Each specialized agent only performs its specific function:
- Math Agent: Only computes and returns mathematical results.
- English Agent: Only explains or summarizes results in plain English.
- Language Agent: Only translates text between languages.
- Computer Science Agent: Only answers programming and computer science questions.
- General Assistant: Only handles general knowledge queries.

For multi-step queries, coordinate multiple agents in sequence, passing outputs as needed. Do not use a single agent for multiple steps.

Additional Instructions:
- When providing routing explanations, be specific and accurate about the type of problem (e.g., "addition" instead of "quadratic equation" for sums).
- Simply call the appropriate tool and let its response be the final answer. Do not add additional commentary or repeat the tool's output.
- The tool response itself is the complete answer to the user.

1. Analyze incoming student queries and determine the most appropriate specialized agent to handle them:
   - Math Agent: For mathematical calculations, problems, and concepts
   - English Agent: For writing, grammar, literature, and composition
   - Language Agent: For translation and language-related queries
   - Computer Science Agent: For programming, algorithms, data structures, and code execution
   - General Assistant: For all other topics outside these specialized domains

2. Key Responsibilities:
   - Accurately classify student queries by subject area
   - Route requests to the appropriate specialized agent
   - Maintain context and coordinate multi-step problems
   - Ensure cohesive responses when multiple agents are needed

3. Decision Protocol:
   - If query involves calculations/numbers → Math Agent
   - If query involves writing/literature/grammar → English Agent
   - If query involves translation → Language Agent
   - If query involves programming/coding/algorithms/computer science → Computer Science Agent
   - If query is outside these specialized areas → General Assistant
   - For complex queries, coordinate multiple agents as needed

When you respond, first state which agent you are using and why, then call the appropriate tool. The tool's response is the final answer - do not repeat or summarize it.
"""

ollama_model = OllamaModel(
    host="http://localhost:11434",  # Ollama server address
    model_id="llama3.2:3b",  # Specify the model
)


class TeacherAssistant:
    """
    A teacher's assistant that routes queries to specialized agents.

    This class can be used programmatically to get responses from the
    multi-agent system without needing the command-line interface.
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model_id: str = "llama3.2:3b",
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize the TeacherAssistant.

        Args:
            host: Ollama server address
            model_id: Model to use for the main orchestrating agent
            system_prompt: Custom system prompt (uses default if None)
        """
        self.model = OllamaModel(host=host, model_id=model_id)
        self.system_prompt = system_prompt or TEACHER_SYSTEM_PROMPT
        self.console = Console()

    def ask(self, query: str, return_metrics: bool = False) -> str:
        """
        Ask a question to the teacher assistant.

        Args:
            query: The question to ask
            return_metrics: Whether to return metrics along with the response

        Returns:
            String response from the agent, or dict with response and metrics
        """
        # Create a fresh agent for each query to clear context
        agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=[
                math_assistant,
                english_assistant,
                language_assistant,
                computer_science_assistant,
                general_assistant,
                today,
            ],
        )

        response = agent(query)
        response_str = str(response)

        # Post-process output to ensure newlines before routing explanations
        response_str = re.sub(r"([^\n])(?=Routing to )", r"\1\n", response_str)

        if return_metrics:
            return {"response": response_str, "metrics": response.metrics.get_summary()}
        return response_str

    def ask_with_console_output(self, query: str, show_metrics: bool = False) -> str:
        """
        Ask a question and print formatted output to console.

        Args:
            query: The question to ask
            show_metrics: Whether to print JSON metrics

        Returns:
            String response from the agent
        """
        result = self.ask(query, return_metrics=True)

        # Print formatted response
        self.console.print(Markdown(result["response"]))

        # Print metrics as JSON if requested
        if show_metrics:
            try:
                print(json.dumps(result["metrics"], indent=4, ensure_ascii=False))
            except Exception as e:
                print(f"Could not print metrics as JSON: {e}")

        return result["response"]


console = Console()

HISTORY_FILE = os.path.expanduser("~/.teachassist_history")


def run_cli():
    """Run the command-line interface for the teacher assistant."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Teacher's Assistant - Multi-agent educational support system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python teachers_assistant.py                    # Run without metrics output (default)
  python teachers_assistant.py --metrics         # Run with metrics output
  python teachers_assistant.py -q "What is 2+2?" # Ask single question and exit
        """,
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Enable JSON metrics output after each response",
    )
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Ask a single question and exit (non-interactive mode)",
    )

    args = parser.parse_args()
    show_metrics = args.metrics

    # Handle single query mode
    if args.query:
        teacher = TeacherAssistant()
        teacher.ask_with_console_output(args.query, show_metrics=show_metrics)
        return

    # Load history if file exists
    if os.path.exists(HISTORY_FILE):
        readline.read_history_file(HISTORY_FILE)

    print("\n📁 Teacher's Assistant Strands Agent 📁\n")
    print(
        "Ask a question in any subject area, and I'll route it to the appropriate specialist."
    )
    print("Type 'exit' to quit.")
    if show_metrics:
        print("📊 JSON metrics output is enabled")

    # Initialize the teacher assistant
    teacher = TeacherAssistant()

    try:
        while True:
            try:
                user_input = input("\n> ")

                # Skip empty input
                if not user_input.strip():
                    continue

                if user_input.lower() in ["exit", "quit"]:
                    print("\nGoodbye! 👋")
                    break

                teacher.ask_with_console_output(user_input, show_metrics=show_metrics)

            except KeyboardInterrupt:
                print("\n\nExecution interrupted. Exiting...")
                break
            except EOFError:
                print("\n\nReceived EOF (Control-D). Exiting...")
                break
            except Exception as e:
                print(f"\nAn error occurred: {str(e)}")
                print("Please try asking a different question.")
    finally:
        # Save history on exit
        readline.write_history_file(HISTORY_FILE)


if __name__ == "__main__":
    run_cli()
