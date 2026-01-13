"""
Storyteller Agent - Main ADK Agent for Comic Book Narration
This agent brings comic books to life through voice for blind users and children.
"""

from datetime import datetime
from typing import Dict, Optional
from google.adk.agents import Agent
from ..config import GEMINI_MODEL, CHILD_MODE
from .prompts import STORYTELLER_PROMPT


def get_current_context(session_state: Dict) -> str:
    """
    Build the current context string for the agent prompt.

    Args:
        session_state: Current session state

    Returns:
        Formatted context string
    """
    comic_data = session_state.get("comic_data", {})
    current_page = session_state.get("current_page", 1)
    total_pages = comic_data.get("page_count", 0)

    if not comic_data:
        return "No comic is currently loaded. Waiting for user to upload a PDF."

    title = comic_data.get("title", "Unknown")

    # Get current page data
    pages = comic_data.get("pages", [])
    current_page_data = None
    for page in pages:
        if page.get("page_number") == current_page:
            current_page_data = page
            break

    context_parts = [
        f"Comic: {title}",
        f"Current Page: {current_page} of {total_pages}",
    ]

    if current_page_data:
        if current_page_data.get("setting"):
            context_parts.append(f"Setting: {current_page_data['setting']}")
        if current_page_data.get("characters_present"):
            context_parts.append(
                f"Characters on page: {', '.join(current_page_data['characters_present'])}"
            )
        if current_page_data.get("narration_script"):
            context_parts.append(
                f"Page content: {current_page_data['narration_script'][:500]}..."
            )

    child_mode = session_state.get("child_mode", CHILD_MODE)
    if child_mode:
        context_parts.append("MODE: Child-friendly (use simple language)")

    return "\n".join(context_parts)


# Tool functions that will be registered with the agent
def navigate_to_page(page_number: int) -> str:
    """
    Navigate to a specific page in the comic.

    Args:
        page_number: The page number to go to (starting from 1)

    Returns:
        Confirmation message
    """
    # This is a placeholder - actual implementation uses session state
    return f"Navigating to page {page_number}."


def next_page() -> str:
    """
    Go to the next page in the comic.

    Returns:
        Confirmation message with new page number
    """
    return "Moving to the next page."


def previous_page() -> str:
    """
    Go to the previous page in the comic.

    Returns:
        Confirmation message with new page number
    """
    return "Going back to the previous page."


def describe_scene() -> str:
    """
    Get a detailed description of the current scene.

    Returns:
        Scene description
    """
    return "Describing the current scene..."


def get_character_info(character_name: str) -> str:
    """
    Get information about a character in the comic.

    Args:
        character_name: The name of the character to look up

    Returns:
        Character information and description
    """
    return f"Looking up information about {character_name}..."


def get_story_summary() -> str:
    """
    Get a summary of the story so far.

    Returns:
        Story summary
    """
    return "Here's what's happened so far..."


def read_current_page() -> str:
    """
    Read/narrate the current page aloud.

    Returns:
        The narration for the current page
    """
    return "Reading the current page..."


def repeat_narration() -> str:
    """
    Repeat the narration of the current page.

    Returns:
        The narration repeated
    """
    return "Repeating the current page..."


def get_help() -> str:
    """
    Get help about available commands.

    Returns:
        Help message with available commands
    """
    return """
Here are the commands I understand:

READING:
- "Read" or "Start" - Begin narration
- "Repeat" - Hear the current page again
- "Stop" or "Pause" - Stop reading

NAVIGATION:
- "Next page" - Go forward
- "Previous page" or "Go back" - Go backward
- "Go to page [number]" - Jump to a specific page
- "Where am I?" - Get current page info

DESCRIPTIONS:
- "Describe this" - Detailed scene description
- "What's happening?" - Quick summary
- "Who is [character]?" - Character information

Just ask me anything about the story!
"""


def create_storyteller_agent(session_state: Optional[Dict] = None) -> Agent:
    """
    Create a new storyteller agent with current context.

    Args:
        session_state: Optional session state for context

    Returns:
        Configured Agent instance
    """
    context = get_current_context(session_state or {})
    instruction = STORYTELLER_PROMPT.format(context=context)

    return Agent(
        name="comic_storyteller",
        model=GEMINI_MODEL,
        description="""An engaging storyteller that brings comic books to life through voice narration.
        Designed specifically for blind people and children, providing vivid descriptions,
        character voices, and interactive story exploration.""",
        instruction=instruction,
        tools=[
            navigate_to_page,
            next_page,
            previous_page,
            describe_scene,
            get_character_info,
            get_story_summary,
            read_current_page,
            repeat_narration,
            get_help,
        ],
    )


# Create a default agent instance
storyteller_agent = create_storyteller_agent()
