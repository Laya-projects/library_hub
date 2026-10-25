"""The category tree and its recursive functions. (Step 7 adds the recursion.)"""

from __future__ import annotations

# Child category -> parent category. Anything not listed is its own top level.
PARENT_CATEGORY = {
    "Programming": "Technology",
    "Software Engineering": "Technology",
}


def top_category(category: str) -> str:
    """The top-level category: Programming and Software Engineering are Technology."""
    return PARENT_CATEGORY.get(category, category)