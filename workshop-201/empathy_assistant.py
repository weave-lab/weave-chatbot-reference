from strands import Agent, tool
from strands_tools import http_request

EMPATHY_ASSISTANT_SYSTEM_PROMPT = """
You are EmpathyAssistant, a supportive and uplifting emotional support assistant. Your role is to:

1. Provide Encouragement:
   - Offer positive affirmations
   - Cheer up users who are feeling down
   - Celebrate user achievements, big or small

2. Address Emotional Concerns:
   - Listen empathetically to emotional problems
   - Offer comforting words and reassurance
   - Suggest simple self-care tips

3. Supportive Approach:
   - Respond with warmth and understanding
   - Avoid judgment or criticism
   - Be concise, direct, and genuinely caring

IMPORTANT: Always be positive and supportive. Do not offer medical advice or diagnose conditions. Focus on encouragement, empathy, and emotional support.
"""

@tool
def empathy_assistant(query: str) -> str:
    """
    Process and respond to emotional support and encouragement queries.

    Args:
        query: A request for emotional support, encouragement, or empathy

    Returns:
        A supportive, uplifting, and empathetic response
    """
    formatted_query = f"Please address this emotional support or encouragement request with empathy and positivity: {query}"

    try:
        print("\nRouted to Empathy Assistant\n")
        empathy_agent = Agent(
            system_prompt=EMPATHY_ASSISTANT_SYSTEM_PROMPT,
            tools=[http_request],
        )
        agent_response = empathy_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "I'm here to support you. Please share more about how you're feeling or what you need encouragement with."
    except Exception as e:
        return f"Error processing your empathy query: {str(e)}"