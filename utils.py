"""utils.py"""

import random
import re
import string

import unicodedata


def random_string(length):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


def format_text(text: str) -> str:
    """
    Format the text to a standardized form.
    :param text: The input text to format.
    :return: The formatted text.
    """

    # Normalize the text to Unicode NFC form
    normalized_text = unicodedata.normalize("NFC", text)

    # Remove non-printable characters
    printable_text = re.sub(r"[^\x20-\x7E]", "", normalized_text)

    # Standardize whitespace
    standardized_whitespace = re.sub(r"\s+", " ", printable_text).strip()

    return standardized_whitespace
