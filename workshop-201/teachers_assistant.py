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
import requests
import sys
from rich.console import Console
from rich.markdown import Markdown
import json
from typing import Optional

TEACHER_SYSTEM_PROMPT = """
CRITICAL INSTRUCTION: Never apologize or make excuses. Be direct and confident. Execute tools immediately and return their results.

MANDATORY ROUTING FOR DATE QUERIES: Any question about "date", "today", "what day", "current date" MUST use the Today Tool. Do NOT route date questions to general_assistant.

For any query, autonomously plan and execute all necessary tool calls in sequence to fully resolve the user's request. Chain outputs between tools as needed, and return the final result. Do not ask the user to perform intermediate steps or confirm actions; handle everything automatically.

Only call the Language Agent if the user explicitly requests a translation or a response in another language. Do not translate or call the Language Agent unless asked.

You are TeachAssist, a sophisticated educational orchestrator designed to coordinate educational support across multiple subjects. Your role is to:

Each specialized agent only performs its specific function:
- Math Agent: Only computes and returns mathematical results.
- English Agent: Only explains or summarizes results in plain English.
- Language Agent: Only translates text between languages.
- Computer Science Agent: Only answers programming and computer science questions.
- General Assistant: Only handles general knowledge queries (NOT date queries).
- Today Tool: ALWAYS use for ANY date-related questions including "What is the date today?", "What date is it?", "Today's date", etc.

For multi-step queries, coordinate multiple agents in sequence, passing outputs as needed. Do not use a single agent for multiple steps.

Additional Instructions:
- When providing routing explanations, be specific and accurate about the type of problem (e.g., "addition" instead of "quadratic equation" for sums).
- Simply call the appropriate tool and let its response be the final answer. Do not add additional commentary or repeat the tool's output.
- The tool response itself is the complete answer to the user.
- DO NOT apologize, make excuses, or explain why something didn't work. Just execute the tool and return the result.

1. Analyze incoming student queries and determine the most appropriate specialized agent to handle them:
   - Math Agent: For mathematical calculations, problems, and concepts
   - English Agent: For writing, grammar, literature, and composition
   - Language Agent: For translation and language-related queries
   - Computer Science Agent: For programming, algorithms, data structures, and code execution
   - Today Tool: For ANY date queries like "What is the date today?", "What date is it?", "Today's date" - NEVER use general_assistant for dates
   - General Assistant: For all other topics outside these specialized domains (excluding date queries)

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
   - If query asks about today's date, current date, or "what date is it" → Today Tool (MANDATORY)
   - If query is outside these specialized areas → General Assistant
   - For complex queries, coordinate multiple agents as needed

When you respond, first state which agent you are using and why, then call the appropriate tool. The tool's response is the final answer - do not repeat or summarize it.
"""


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
        max_retries = 3

        for attempt in range(max_retries):
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

            # Check if we got tool call JSON instead of actual execution
            if self._is_tool_call_json(response_str):
                if attempt < max_retries - 1:
                    print(
                        f"Tool call not executed, retrying... (attempt {attempt + 1})"
                    )
                    continue
                else:
                    # Final attempt failed, return a helpful message
                    return "I'm having trouble executing the appropriate tool. Please try rephrasing your question or try again."

            # Post-process output to ensure newlines before routing explanations
            response_str = re.sub(r"([^\n])(?=Routing to )", r"\1\n", response_str)

            if return_metrics:
                metrics = {}
                if hasattr(response, "metrics"):
                    try:
                        # Try to get summary if available
                        if hasattr(response.metrics, "get_summary"):
                            metrics = response.metrics.get_summary()
                        else:
                            # Convert metrics object to dict if possible
                            metrics = (
                                vars(response.metrics)
                                if hasattr(response.metrics, "__dict__")
                                else {}
                            )
                    except Exception:
                        # If metrics can't be serialized, provide basic info
                        metrics = {
                            "error": "Metrics not serializable",
                            "type": str(type(response.metrics)),
                        }

                return {"response": response_str, "metrics": metrics}
            return response_str

        # This shouldn't be reached, but just in case
        return "Unable to process your request after multiple attempts."

    def _is_tool_call_json(self, response: str) -> bool:
        """
        Check if the response contains tool call JSON instead of actual execution results.

        Args:
            response: The response string to check

        Returns:
            True if the response appears to be tool call JSON, False otherwise
        """
        # Check for patterns that indicate tool call JSON rather than execution
        json_patterns = [
            '{"name":"math_assistant"',
            '{"name":"computer_science_assistant"',
            '{"name":"english_assistant"',
            '{"name":"language_assistant"',
            '{"name":"general_assistant"',
            '{"name":"today"',
            '"parameters":',
        ]

        # If response contains these patterns and lacks actual content, it's likely JSON
        has_json_pattern = any(pattern in response for pattern in json_patterns)

        # Check if response is very short and mostly JSON-like
        is_short_json = len(response.strip()) < 200 and has_json_pattern

        # Check if response starts with JSON pattern (common case)
        starts_with_json = response.strip().startswith('{"name":')

        return has_json_pattern and (is_short_json or starts_with_json)

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


def check_ollama_health(host: str = "http://localhost:11434", timeout: int = 5) -> bool:
    """
    Check if Ollama is running and accessible.

    Args:
        host: Ollama server address
        timeout: Request timeout in seconds

    Returns:
        True if Ollama is accessible, False otherwise
    """
    try:
        response = requests.get(f"{host}/api/tags", timeout=timeout)
        return response.status_code == 200
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.RequestException,
    ):
        return False


def fail_fast_ollama_check(host: str = "http://localhost:11434"):
    """
    Check if Ollama is running and exit immediately if not.

    Args:
        host: Ollama server address
    """
    print("Checking Ollama connection...")

    if not check_ollama_health(host):
        console.print(
            f"[red]❌ Error: Ollama is not running or not accessible at {host}[/red]"
        )
        console.print(
            "\n[yellow]Please ensure Ollama is installed and running:[/yellow]"
        )
        console.print("1. Install Ollama from https://ollama.com/download")
        console.print("2. Start Ollama by running: ollama serve")
        console.print("3. Pull the required model: ollama pull llama3.2:3b")
        console.print("\nThen try running the teacher assistant again.")
        sys.exit(1)

    print("✅ Ollama connection successful")


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

    # Fail fast if Ollama is not running
    fail_fast_ollama_check()

    # Handle single query mode
    if args.query:
        teacher = TeacherAssistant()
        teacher.ask_with_console_output(args.query, show_metrics=show_metrics)
        return

    # Load history if file exists
    if os.path.exists(HISTORY_FILE):
        readline.read_history_file(HISTORY_FILE)

    # Configure readline for better history handling
    readline.set_history_length(1000)
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")

    # Clear any potential readline artifacts
    readline.clear_history()
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
