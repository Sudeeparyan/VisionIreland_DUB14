"""
Storytelling Tools - Tools for narration and storytelling
"""

from typing import Dict, Optional
from ..agents.prompts import ACCESSIBILITY_RESPONSES


def get_page_narration(
    comic_data: Dict, page_number: int, child_mode: bool = False
) -> Dict:
    """
    Get the narration script for a specific page.

    Args:
        comic_data: The parsed comic data
        page_number: The page to narrate
        child_mode: If True, use simpler language

    Returns:
        Narration script and metadata
    """
    pages = comic_data.get("pages", [])

    # Find the page
    page_data = None
    for page in pages:
        if page.get("page_number") == page_number:
            page_data = page
            break

    if not page_data:
        return {
            "success": False,
            "message": f"Page {page_number} not found.",
            "narration": "",
        }

    narration = page_data.get("narration_script", "")

    # Build a structured narration if script is missing
    if not narration:
        parts = []

        # Page announcement
        total = comic_data.get("page_count", len(pages))
        parts.append(f"Page {page_number} of {total}.")

        # Setting
        if page_data.get("setting"):
            parts.append(page_data["setting"])

        # Action
        if page_data.get("action_summary"):
            parts.append(page_data["action_summary"])

        narration = " ".join(parts)

    # Add page position context
    total_pages = comic_data.get("page_count", len(pages))

    position_context = ""
    if page_number == 1:
        title = comic_data.get("title", "this story")
        position_context = f"Beginning of {title}. "
    elif page_number == total_pages:
        position_context = "The final page. "

    return {
        "success": True,
        "page_number": page_number,
        "total_pages": total_pages,
        "narration": position_context + narration,
        "setting": page_data.get("setting", ""),
        "characters": page_data.get("characters_present", []),
        "is_first_page": page_number == 1,
        "is_last_page": page_number == total_pages,
    }


def get_welcome_message(comic_data: Optional[Dict] = None) -> str:
    """
    Get the welcome message for new users.

    Args:
        comic_data: Optional comic data if a comic is loaded

    Returns:
        Welcome message string
    """
    if comic_data:
        title = comic_data.get("title", "your comic")
        author = comic_data.get("author", "")
        page_count = comic_data.get("page_count", 0)

        author_text = f" by {author}" if author and author != "Unknown" else ""

        return f"""Welcome! I've loaded "{title}"{author_text}. 
It has {page_count} pages of adventure waiting for you!

You can say:
- "Start" or "Read" to begin the story
- "Describe" to hear about the cover
- "Help" for all available commands

Ready to begin?"""

    return ACCESSIBILITY_RESPONSES["welcome"]


def get_help_message() -> str:
    """
    Get the help message with available commands.

    Returns:
        Help message string
    """
    return ACCESSIBILITY_RESPONSES["help"]


def format_page_transition(
    from_page: int, to_page: int, direction: str, comic_data: Dict
) -> str:
    """
    Format a smooth transition message between pages.

    Args:
        from_page: Previous page number
        to_page: New page number
        direction: "forward", "backward", or "jump"
        comic_data: The parsed comic data

    Returns:
        Transition message
    """
    total = comic_data.get("page_count", 0)
    pages = comic_data.get("pages", [])

    # Get brief context for new page
    new_page_data = None
    for page in pages:
        if page.get("page_number") == to_page:
            new_page_data = page
            break

    brief_context = ""
    if new_page_data:
        if new_page_data.get("setting"):
            brief_context = new_page_data["setting"]
        elif new_page_data.get("action_summary"):
            # Take first sentence
            summary = new_page_data["action_summary"]
            brief_context = summary.split(".")[0] + "."

    if direction == "forward":
        transition = f"Turning to page {to_page}. "
    elif direction == "backward":
        transition = f"Going back to page {to_page}. "
    else:  # jump
        transition = f"Jumping to page {to_page} of {total}. "

    if brief_context:
        transition += brief_context

    return transition


def format_story_ending(comic_data: Dict) -> str:
    """
    Format the ending message when the story concludes.

    Args:
        comic_data: The parsed comic data

    Returns:
        Ending message
    """
    title = comic_data.get("title", "the story")

    return f"""
And that concludes {title}!

What an adventure! You can:
- Say "start" to read it again from the beginning
- Say "go to page [number]" to revisit a favorite part
- Ask me about any character or scene
- Or upload a new comic to explore!

Thank you for experiencing this story with me. What would you like to do next?
"""


def format_chapter_summary(comic_data: Dict, start_page: int, end_page: int) -> str:
    """
    Create a summary of pages in a range.

    Args:
        comic_data: The parsed comic data
        start_page: First page of range
        end_page: Last page of range

    Returns:
        Summary of the page range
    """
    pages = comic_data.get("pages", [])

    summaries = []
    for page in pages:
        pnum = page.get("page_number", 0)
        if start_page <= pnum <= end_page:
            if page.get("action_summary"):
                summaries.append(page["action_summary"])

    if not summaries:
        return f"Pages {start_page} to {end_page} of the story."

    return " ".join(summaries)
