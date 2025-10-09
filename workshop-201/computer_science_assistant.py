from strands import Agent, tool
from strands_tools import python_repl, shell, file_read, file_write, editor
from strands.models.gemini import GeminiModel

COMPUTER_SCIENCE_ASSISTANT_SYSTEM_PROMPT = """
You are ComputerScienceExpert, a specialized assistant for computer science education and programming. Your capabilities include:

1. Programming Support:
   - Code explanation and debugging
   - Algorithm development and optimization
   - Software design patterns implementation
   - Programming language syntax guidance

2. Computer Science Education:
   - Theoretical concepts explanation
   - Data structures and algorithms teaching
   - Computer architecture fundamentals
   - Networking and security principles

3. Technical Assistance:
   - Real-time code execution and testing
   - Shell command guidance and execution
   - File system operations and management
   - Code editing and improvement suggestions

4. Teaching Methodology:
   - Step-by-step explanations with examples
   - Progressive concept building
   - Interactive learning through code execution
   - Real-world application demonstrations

Focus on providing clear, practical explanations that demonstrate concepts with executable examples. Use code execution tools to illustrate concepts whenever possible.

IMPORTANT: Be direct and confident in your responses. Do not apologize or make excuses. Simply provide the requested information or solution clearly and efficiently.
"""


@tool
def computer_science_assistant(query: str) -> str:
    """
    Process and respond to computer science and programming-related questions using a specialized agent with code execution capabilities.

    Args:
        query: The user's computer science or programming question

    Returns:
        A detailed response addressing computer science concepts or code execution results
    """
    # Format the query for the computer science agent with clear instructions
    formatted_query = f"Please address this computer science or programming question. When appropriate, provide executable code examples and explain the concepts thoroughly: {query}"

    try:
        print("Routed to Computer Science Assistant")

        model = GeminiModel(
            client_args={
                "project": "weave-ai-sandbox",
                "location": "us-central1",
                "vertexai": True,
            },
            model_id="gemini-2.5-flash",
        )

        # Create the computer science agent with relevant tools
        cs_agent = Agent(
            model=model,
            system_prompt=COMPUTER_SCIENCE_ASSISTANT_SYSTEM_PROMPT,
            tools=[python_repl, shell, file_read, file_write, editor],
        )
        agent_response = cs_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "Unable to process your computer science question. Try rephrasing or providing more specific details."
    except Exception as e:
        # Return specific error message for computer science processing
        return f"Error processing your computer science query: {str(e)}"
