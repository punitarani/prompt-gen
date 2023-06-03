"""
gen.py

Prompt-Generation Generator
"""

import asyncio
import random

from utils import random_string


async def generate_prompt_generations(base_prompt):
    """Generate prompt generations"""
    # TODO: Implement this
    await asyncio.sleep(random.uniform(0.5, 2))
    return {
        "prompt": base_prompt + " " + random_string(8),
        "generation": random_string(32),
    }
