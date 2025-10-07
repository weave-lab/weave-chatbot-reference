from strands import Agent, tool
from strands_tools import file_read, file_write, editor

ENGLISH_ASSISTANT_SYSTEM_PROMPT = """
You are English master, an advanced English education assistant. Your capabilities include:

1. Writing Support:
   - Grammar and syntax improvement
   - Vocabulary enhancement
   - Style and tone refinement
   - Structure and organization guidance

2. Analysis Tools:
   - Text summarization
   - Literary analysis
   - Content evaluation
   - Citation assistance

3. Teaching Methods:
   - Provide clear explanations with examples
   - Offer constructive feedback
   - Suggest improvements
   - Break down complex concepts

Focus on being clear, encouraging, and educational in all interactions. Always explain the reasoning behind your suggestions to promote learning.

IMPORTANT: Be direct and confident in your responses. Do not apologize or make excuses. Simply provide the requested analysis, feedback, or assistance clearly and efficiently.
"""


@tool
def english_assistant(query: str) -> str:
    """
    Process and respond to English language, literature, and writing-related queries.

    Args:
        query: The user's English language or literature question

    Returns:
        A helpful response addressing English language or literature concepts
    """
    # Format the query with specific guidance for the English assistant
    formatted_query = f"Analyze and respond to this English language or literature question, providing clear explanations with examples where appropriate: {query}"

    try:
        print("Routed to English Assistant")

        english_agent = Agent(
            system_prompt=ENGLISH_ASSISTANT_SYSTEM_PROMPT,
            tools=[editor, file_read, file_write],
        )
        agent_response = english_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "Unable to analyze the English language question. Please rephrase or provide more context."
    except Exception as e:
        # Return specific error message for English queries
        return f"Error processing your English language query: {str(e)}"
