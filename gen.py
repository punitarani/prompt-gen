"""
gen.py

Prompt-Generation Generator
"""

import asyncio
import random

from utils import random_string


async def generate_prompt_generations(base_prompt: str):
    """Generate prompt generations"""
    # TODO: Implement this
    await asyncio.sleep(random.uniform(0.5, 2))
    return {
        "prompt": random_string(8),
        "generation": base_prompt,
    }
