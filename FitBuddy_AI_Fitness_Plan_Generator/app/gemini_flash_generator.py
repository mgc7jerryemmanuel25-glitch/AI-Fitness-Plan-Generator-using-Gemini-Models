from .config import get_settings
from .gemini_client import generate_text


def generate_nutrition_tip_with_flash(goal: str) -> str:
    settings = get_settings()

    prompt = f"""
You are FitBuddy's nutrition and recovery assistant.

Fitness goal: {goal}

Give ONE concise, practical nutrition or recovery tip that complements this goal.
Keep it to 2–4 sentences. Favor balanced meals, hydration, adequate recovery,
and ordinary food choices. Do not prescribe medication or supplements, and do
not diagnose health conditions.
"""
    return generate_text(prompt, settings["tip_model"])
