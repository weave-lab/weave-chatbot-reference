from strands import Agent, tool
from strands_tools import http_request

DREAM_INTERPRETER_ASSISTANT_SYSTEM_PROMPT = """
You are DreamInterpreterAssistant, a specialized dream interpretation assistant. Your role encompasses:

1. Dream Analysis:
   - Analyze and interpret dream content
   - Identify symbols and themes
   - Provide psychological insights

2. Cultural Context:
   - Explain cultural significance of dream elements
   - Discuss historical interpretations
   - Offer diverse perspectives

3. Personal Guidance:
   - Relate dream insights to personal experiences
   - Suggest practical applications of interpretations
   - Encourage self-reflection and exploration

Maintain sensitivity and respect for diverse beliefs about dreams.

IMPORTANT: Be direct and confident in your responses. Do not apologize or make excuses. Simply provide the requested interpretation or guidance clearly and efficiently.
"""


@tool
def dream_interpreter(query: str) -> str:
    """
    Process and respond to dream interpretation queries.

    Args:
        query: A request for dream analysis or interpretation

    Returns:
        A dream interpretation or guidance with explanations
    """
    # Format the query with specific guidance for the dream interpreter
    formatted_query = f"Please address this dream interpretation request, providing cultural context and explanations where helpful: {query}"

    try:
        print("\nRouted to Dream Interpreter\n")
        dream_agent = Agent(
            system_prompt=DREAM_INTERPRETER_ASSISTANT_SYSTEM_PROMPT,
            tools=[http_request],
        )
        agent_response = dream_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "Unable to process your dream interpretation request. Please provide more details about the dream."
    except Exception as e:
        # Return specific error message for dream processing
        return f"Error processing your dream query: {str(e)}"

