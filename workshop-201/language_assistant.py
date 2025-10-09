from strands import Agent, tool
from strands_tools import http_request
from strands.models.gemini import GeminiModel

LANGUAGE_ASSISTANT_SYSTEM_PROMPT = """
You are LanguageAssistant, a specialized language translation and learning assistant. Your role encompasses:

1. Translation Services:
   - Accurate translation between languages
   - Context-appropriate translations
   - Idiomatic expression handling
   - Cultural context consideration

2. Language Learning Support:
   - Explain translation choices
   - Highlight language patterns
   - Provide pronunciation guidance
   - Cultural context explanations

3. Teaching Approach:
   - Break down translations step-by-step
   - Explain grammar differences
   - Provide relevant examples
   - Offer learning tips

Maintain accuracy while ensuring translations are natural and contextually appropriate.

IMPORTANT: Be direct and confident in your responses. Do not apologize or make excuses. Simply provide the requested translation or language assistance clearly and efficiently.
"""


@tool
def language_assistant(query: str) -> str:
    """
    Process and respond to language translation and foreign language learning queries.

    Args:
        query: A request for translation or language learning assistance

    Returns:
        A translated text or language learning guidance with explanations
    """
    # Format the query with specific guidance for the language assistant
    formatted_query = f"Please address this translation or language learning request, providing cultural context and explanations where helpful: {query}"

    try:
        print("\nRouted to Language Assistant\n")

        model = GeminiModel(
            client_args={
                "project": "weave-ai-sandbox",
                "location": "us-central1",
                "vertexai": True,
            },
            model_id="gemini-2.5-flash",
        )

        language_agent = Agent(
            model=model,
            system_prompt=LANGUAGE_ASSISTANT_SYSTEM_PROMPT,
            tools=[http_request],
        )
        agent_response = language_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "Unable to process your language request. Please specify the languages involved and the specific translation or learning need."
    except Exception as e:
        # Return specific error message for language processing
        return f"Error processing your language query: {str(e)}"
