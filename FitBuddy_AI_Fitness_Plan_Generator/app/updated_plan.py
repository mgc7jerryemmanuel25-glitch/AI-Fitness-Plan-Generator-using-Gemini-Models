from .config import get_settings
from .gemini_client import generate_text


def update_workout_plan(original_plan: str, user_feedback: str) -> str:
    settings = get_settings()

    prompt = f"""
You are FitBuddy, a responsible fitness-planning assistant.

Original 7-day workout plan:
--- START ---
{original_plan}
--- END ---

User feedback:
{user_feedback}

Revise the plan according to the feedback.
Rules:
- Keep the 7-day structure.
- Preserve useful parts that do not need changing.
- Make requested changes clear.
- Keep intensity and workload sensible.
- Include warm-up, main workout, recovery/rest and cooldown where appropriate.
- Do not diagnose injuries or medical conditions.
- Do not prescribe medication or supplements.
- If feedback indicates pain, injury, or a medical issue, recommend professional
  evaluation rather than attempting a diagnosis.
- Return only the revised plan with readable headings.
"""
    return generate_text(prompt, settings["workout_model"])
