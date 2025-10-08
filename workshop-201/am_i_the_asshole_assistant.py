from strands import Agent, tool

AMTA_ASSISTANT_SYSTEM_PROMPT = """
You are a judgmental modern internet user with above average interpersonal skills. Your capabilities include:

1. Having lots of knowledge about interpersonal conflicts:
   - Understanding different perspectives
   - Analyzing social dynamics
   - Identifying problematic behavior
   - Offering constructive feedback

2. Ability to use harsh language to make judgment without using profanity or slurs:
   - Blunt critiques
   - Sarcasm
   - Dismissive remarks
   - Cutting observations

3. Social and Cultural Awareness:
   - Understanding social norms and expectations
   - Recognizing patterns of behavior
   - Identifying red flags in relationships
   - Providing reality checks when needed

Focus on concluding who is in the wrong in a given situation while expanding on your reasons.
Format your response in casual language as if you were posting on a social media forum. Avoid sounding formal, polished,
or academic. Use a conversational tone that is relatable and engaging. 

IMPORTANT: Be confident in your responses. Do not apologize or make excuses. Don't equivocate.
"""


@tool
def am_i_the_asshole_assistant(query: str) -> str:
    """
    Analyzes a given interpersonal scenario and determines the appropriate "Am I the Asshole" (AITA) judgment.

    Parameters:
        query (str): A description of the interpersonal scenario to be evaluated.

    Returns:
        str: The AITA judgment ("Not the asshole", "You're the asshole", "Everyone sucks here", "No assholes here", or "Info needed") 
             followed by an explanation, or an error message if the query cannot be processed.

    Raises:
        Exception: Returns an error message if there is an issue processing the query.
    """
    # Format the query for the AITA agent with clear instructions
    formatted_query = f"""Determine in the following scenario and determine if people in the scenario are being rude, impolite, or inconsiderate.
    You can make one of the following judgments:
    - "Not the asshole" - if the person is not in the wrong
    - "You're the asshole" - if the person is in the wrong
    - "Everyone sucks here" - if everyone is in the wrong
    - "No assholes here" - if no one is in the wrong
    - "Info needed" - if you need more information to make a judgment
    Start your response with one of these judgments and then explain your reasoning for it. Scenario: {query}"""

    try:
        print("Routed to Am I the Asshole Assistant")
        # Create the AITA agent (no tools needed for interpersonal judgment)
        aita_agent = Agent(
            system_prompt=AMTA_ASSISTANT_SYSTEM_PROMPT
        )
        agent_response = aita_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "Unable to solve this interpersonal problem. Please check if your query is clearly stated or try rephrasing it."
    except Exception as e:
        # Return specific error message for AITA processing
        return f"Error processing your interpersonal query: {str(e)}"
