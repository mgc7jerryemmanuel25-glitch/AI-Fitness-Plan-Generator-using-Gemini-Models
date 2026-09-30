from .config import get_settings
from .gemini_client import generate_text


def generate_workout_gemini(user_data: dict) -> str:
    settings = get_settings()

    prompt = f"""
You are FitBuddy, a responsible fitness-planning assistant.

Create a structured 7-day general fitness plan using:
Name: {user_data["name"]}
Age: {user_data["age"]}
Weight: {user_data["weight"]} kg
Fitness goal: {user_data["goal"]}
Workout intensity: {user_data["intensity"]}

Requirements:
- Provide Day 1 through Day 7.
- For training days include a 5–10 minute warm-up, main workout,
  sets/repetitions or duration, rest guidance, and cooldown/recovery.
- Include appropriate recovery/rest days.
- Scale workload to the requested intensity.
- Keep the plan practical for a general user.
- Do not diagnose, treat, or claim to cure medical conditions.
- Do not prescribe medication or supplements.
- If an exercise causes pain, advise stopping and seeking appropriate advice.
- Use clear headings and plain text.
"""
    return generate_text(prompt, settings["workout_model"])
