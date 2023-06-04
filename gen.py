"""
gen.py

Prompt-Generation Generator
"""

import json
import os

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


async def generate_prompt_generations(prompt: str) -> list[dict]:
    """Generate prompt generations"""
    completion = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(completion.choices[0].message.content).get("response", {})
