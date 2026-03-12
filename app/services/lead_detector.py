"""
Hot-lead detection — keyword scanning for high-intent student messages.
"""

import re

# Keywords that signal a student is a high-intent ("hot") lead.
HOT_LEAD_KEYWORDS: list[str] = [
    "fees",
    "fee",
    "admission",
    "admit",
    "placement",
    "placements",
    "seat",
    "seats",
    "apply",
    "application",
    "hostel",
    "scholarship",
    "cutoff",
    "cut off",
    "cut-off",
    "last date",
    "deadline",
    "merit",
    "counselling",
    "counseling",
]

# Pre-compile a single regex for efficient matching.
_pattern = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in HOT_LEAD_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def detect_hot_lead(message_text: str) -> bool:
    """
    Check if a student message contains high-intent keywords.

    Args:
        message_text: The raw text message from the student.

    Returns:
        True if any hot-lead keyword is found; False otherwise.
    """
    if not message_text:
        return False
    return bool(_pattern.search(message_text))
