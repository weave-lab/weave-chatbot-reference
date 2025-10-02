from strands import tool
from datetime import datetime

@tool
def today() -> str:
    """
    Returns today's date in a human-readable format.

    Returns:
        A string representing today's date.
    """
    return datetime.now().strftime("%B %d, %Y")