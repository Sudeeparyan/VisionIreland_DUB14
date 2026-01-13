"""
Navigation Tools - Tools for navigating through the comic book
"""

from typing import Dict, Optional

# Session state will be managed by the main app
# These functions work with a comic_session object


def navigate_to_page(comic_session: Dict, page_number: int) -> Dict:
    """
    Navigate to a specific page number.

    Args:
        comic_session: The current session state
        page_number: The page number to navigate to (1-indexed)

    Returns:
        Result dictionary with success status and page info
    """
    total_pages = comic_session.get("total_pages", 0)

    if page_number < 1:
        return {
            "success": False,
            "message": "Page number must be at least 1.",
            "current_page": comic_session.get("current_page", 1),
        }

    if page_number > total_pages:
        return {
            "success": False,
            "message": f"This comic only has {total_pages} pages. You asked for page {page_number}.",
            "current_page": comic_session.get("current_page", 1),
        }

    comic_session["current_page"] = page_number

    return {
        "success": True,
        "message": f"Now on page {page_number} of {total_pages}.",
        "current_page": page_number,
        "total_pages": total_pages,
    }


def get_current_page(comic_session: Dict) -> Dict:
    """
    Get information about the current page.

    Args:
        comic_session: The current session state

    Returns:
        Dictionary with current page information
    """
    current = comic_session.get("current_page", 1)
    total = comic_session.get("total_pages", 0)

    return {
        "current_page": current,
        "total_pages": total,
        "message": f"You are on page {current} of {total}.",
        "is_first_page": current == 1,
        "is_last_page": current == total,
    }


def get_total_pages(comic_session: Dict) -> int:
    """
    Get the total number of pages in the comic.

    Args:
        comic_session: The current session state

    Returns:
        Total page count
    """
    return comic_session.get("total_pages", 0)


def go_to_next_page(comic_session: Dict) -> Dict:
    """
    Navigate to the next page.

    Args:
        comic_session: The current session state

    Returns:
        Result dictionary with success status and page info
    """
    current = comic_session.get("current_page", 1)
    total = comic_session.get("total_pages", 0)

    if current >= total:
        return {
            "success": False,
            "message": "You're already on the last page. Say 'go to page 1' to start over, or ask me anything about the story!",
            "current_page": current,
            "is_last_page": True,
        }

    new_page = current + 1
    comic_session["current_page"] = new_page

    return {
        "success": True,
        "message": f"Moving to page {new_page}.",
        "current_page": new_page,
        "previous_page": current,
        "is_last_page": new_page == total,
    }


def go_to_previous_page(comic_session: Dict) -> Dict:
    """
    Navigate to the previous page.

    Args:
        comic_session: The current session state

    Returns:
        Result dictionary with success status and page info
    """
    current = comic_session.get("current_page", 1)

    if current <= 1:
        return {
            "success": False,
            "message": "You're already on the first page. Say 'next' to continue, or 'describe' to hear more about this page.",
            "current_page": current,
            "is_first_page": True,
        }

    new_page = current - 1
    comic_session["current_page"] = new_page

    return {
        "success": True,
        "message": f"Going back to page {new_page}.",
        "current_page": new_page,
        "is_first_page": new_page == 1,
    }


def get_reading_progress(comic_session: Dict) -> Dict:
    """
    Get the user's reading progress.

    Args:
        comic_session: The current session state

    Returns:
        Progress information
    """
    current = comic_session.get("current_page", 1)
    total = comic_session.get("total_pages", 0)

    if total == 0:
        return {
            "progress_percent": 0,
            "pages_read": 0,
            "pages_remaining": 0,
            "message": "No comic loaded yet.",
        }

    progress = (current / total) * 100

    if progress < 25:
        encouragement = "You're just getting started!"
    elif progress < 50:
        encouragement = "Great progress! The story is unfolding."
    elif progress < 75:
        encouragement = "More than halfway through! What do you think so far?"
    elif progress < 100:
        encouragement = "Almost there! The finale awaits."
    else:
        encouragement = "You've finished the comic!"

    return {
        "progress_percent": round(progress, 1),
        "current_page": current,
        "total_pages": total,
        "pages_remaining": total - current,
        "message": f"Page {current} of {total} ({round(progress)}% complete). {encouragement}",
    }
