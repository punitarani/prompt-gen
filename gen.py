"""
gen.py

Prompt-Generation Generator
"""

from utils import random_string


def generate_prompt_generations(base_prompt, keywords):
    """Generate prompt generations"""
    # TODO: Implement this
    return {
        "prompt": base_prompt + " " + random_string(10),
        "generation": keywords + " " + random_string(20)
    }
