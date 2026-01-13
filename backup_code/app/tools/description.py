"""
Description Tools - Tools for describing scenes and characters
"""

from typing import Dict, Optional, List


def describe_current_scene(
    comic_session: Dict, comic_data: Dict, detail_level: str = "standard"
) -> Dict:
    """
    Get a description of the current scene/page.

    Args:
        comic_session: The current session state
        comic_data: The parsed comic data
        detail_level: "brief", "standard", or "full"

    Returns:
        Scene description
    """
    current_page = comic_session.get("current_page", 1)
    pages = comic_data.get("pages", [])

    # Find the current page data
    page_data = None
    for page in pages:
        if page.get("page_number") == current_page:
            page_data = page
            break

    if not page_data:
        return {
            "success": False,
            "message": f"I couldn't find information about page {current_page}.",
            "description": "",
        }

    # Build description based on detail level
    if detail_level == "brief":
        description = page_data.get("action_summary", "")
        if not description:
            description = "A scene from the comic."

    elif detail_level == "full":
        parts = []

        # Setting
        if page_data.get("setting"):
            parts.append(f"Setting: {page_data['setting']}")

        # Characters
        if page_data.get("characters_present"):
            chars = ", ".join(page_data["characters_present"])
            parts.append(f"Characters present: {chars}")

        # Narration
        if page_data.get("narration_script"):
            parts.append(f"Scene: {page_data['narration_script']}")

        # Action
        if page_data.get("action_summary"):
            parts.append(f"Summary: {page_data['action_summary']}")

        description = "\n\n".join(parts)

    else:  # standard
        description = page_data.get("narration_script", "")
        if not description:
            description = page_data.get("action_summary", "A scene from the comic.")

    return {
        "success": True,
        "page_number": current_page,
        "description": description,
        "setting": page_data.get("setting", ""),
        "characters": page_data.get("characters_present", []),
    }


def get_character_info(comic_data: Dict, character_name: str) -> Dict:
    """
    Get information about a specific character.

    Args:
        comic_data: The parsed comic data
        character_name: Name of the character to look up

    Returns:
        Character information
    """
    characters = comic_data.get("characters", {})

    # Try exact match first
    if character_name in characters:
        char = characters[character_name]
        return {
            "success": True,
            "name": character_name,
            "description": char.get("description", "No description available."),
            "voice_style": char.get("voice_style", "neutral"),
            "appearances": char.get("appearances", []),
        }

    # Try case-insensitive match
    for name, char in characters.items():
        if name.lower() == character_name.lower():
            return {
                "success": True,
                "name": name,
                "description": char.get("description", "No description available."),
                "voice_style": char.get("voice_style", "neutral"),
                "appearances": char.get("appearances", []),
            }

    # Try partial match
    matches = []
    for name in characters.keys():
        if character_name.lower() in name.lower():
            matches.append(name)

    if matches:
        return {
            "success": False,
            "message": f"I didn't find '{character_name}', but did you mean: {', '.join(matches)}?",
            "suggestions": matches,
        }

    return {
        "success": False,
        "message": f"I don't have information about a character named '{character_name}'.",
        "available_characters": list(characters.keys()),
    }


def get_story_summary(comic_data: Dict, up_to_page: Optional[int] = None) -> Dict:
    """
    Get a summary of the story.

    Args:
        comic_data: The parsed comic data
        up_to_page: If provided, summarize only up to this page

    Returns:
        Story summary
    """
    title = comic_data.get("title", "This comic")
    author = comic_data.get("author", "Unknown")
    synopsis = comic_data.get("synopsis", "")
    pages = comic_data.get("pages", [])

    if up_to_page:
        # Build summary from action summaries
        summaries = []
        for page in pages:
            if page.get("page_number", 0) <= up_to_page:
                if page.get("action_summary"):
                    summaries.append(page["action_summary"])

        if summaries:
            story_so_far = " ".join(summaries)
            return {
                "success": True,
                "title": title,
                "summary": f"So far in {title}: {story_so_far}",
                "pages_covered": up_to_page,
            }

    # Return full synopsis
    return {
        "success": True,
        "title": title,
        "author": author,
        "synopsis": synopsis or f"An adventure story by {author}.",
        "page_count": len(pages),
    }


def list_characters(comic_data: Dict) -> Dict:
    """
    List all characters in the comic.

    Args:
        comic_data: The parsed comic data

    Returns:
        List of characters
    """
    characters = comic_data.get("characters", {})

    if not characters:
        return {
            "success": True,
            "message": "I haven't identified specific characters yet.",
            "characters": [],
        }

    char_list = []
    for name, info in characters.items():
        char_list.append(
            {
                "name": name,
                "description": info.get("description", ""),
            }
        )

    return {
        "success": True,
        "message": f"There are {len(char_list)} characters in this comic.",
        "characters": char_list,
    }


def get_page_context(comic_data: Dict, page_number: int) -> Dict:
    """
    Get context information for a specific page.

    Args:
        comic_data: The parsed comic data
        page_number: The page to get context for

    Returns:
        Context information including previous page summary
    """
    pages = comic_data.get("pages", [])
    total_pages = len(pages)

    context = {
        "page_number": page_number,
        "total_pages": total_pages,
        "is_first_page": page_number == 1,
        "is_last_page": page_number == total_pages,
        "previous_summary": "",
        "current_setting": "",
    }

    for page in pages:
        pnum = page.get("page_number", 0)

        if pnum == page_number - 1:
            context["previous_summary"] = page.get("action_summary", "")

        if pnum == page_number:
            context["current_setting"] = page.get("setting", "")
            context["characters_present"] = page.get("characters_present", [])

    return context
