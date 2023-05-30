"""
gen.py

Prompt-Generation Generator
"""

import asyncio
import random

from utils import random_string


async def generate_prompt_generations(base_prompt, keywords):
    """Generate prompt generations"""
    # TODO: Implement this
    await asyncio.sleep(random.uniform(0.5, 2))
    print("generate_prompt_generations", base_prompt, keywords)
    return {
        "prompt": base_prompt + " " + random_string(10),
        "generation": keywords + " " + random_string(20)
    }
