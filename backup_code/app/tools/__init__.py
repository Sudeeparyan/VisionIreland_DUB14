"""
Tools Module - Agent Tools for Comic Navigation and Interaction
"""

from .navigation import (
    navigate_to_page,
    get_current_page,
    get_total_pages,
    go_to_next_page,
    go_to_previous_page,
)
from .description import (
    describe_current_scene,
    get_character_info,
    get_story_summary,
)
from .storytelling import (
    get_page_narration,
    get_welcome_message,
    get_help_message,
)

__all__ = [
    "navigate_to_page",
    "get_current_page",
    "get_total_pages",
    "go_to_next_page",
    "go_to_previous_page",
    "describe_current_scene",
    "get_character_info",
    "get_story_summary",
    "get_page_narration",
    "get_welcome_message",
    "get_help_message",
]
