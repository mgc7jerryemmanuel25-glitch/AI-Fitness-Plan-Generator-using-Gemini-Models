import time
from functools import lru_cache

from google import genai

from .config import get_settings


@lru_cache
def get_client():
    settings = get_settings()

    if not settings["google_api_key"]:
        return None

    return genai.Client(api_key=settings["google_api_key"])


def generate_text(prompt: str, model: str) -> str:
    settings = get_settings()

    # Demo mode
    if settings["demo_mode"] or not settings["google_api_key"]:
        return demo_response(prompt)

    client = get_client()

    if client is None:
        raise RuntimeError("GOOGLE_API_KEY is not configured.")

    # Retry temporary Gemini availability/rate-limit errors.
    max_attempts = 4
    delays = [2, 4, 8]

    last_error = None

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            text = getattr(response, "text", None)

            if not text:
                raise RuntimeError("Gemini returned an empty response.")

            return text.strip()

        except Exception as error:
            last_error = error
            error_text = str(error)

            # Retry only temporary errors.
            is_temporary = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
                or "500" in error_text
                or "INTERNAL" in error_text
            )

            if not is_temporary:
                raise

            # Stop after the final attempt.
            if attempt == max_attempts - 1:
                break

            wait_time = delays[attempt]

            print(
                f"Gemini temporarily unavailable. "
                f"Retrying in {wait_time} seconds "
                f"(attempt {attempt + 2}/{max_attempts})..."
            )

            time.sleep(wait_time)

    raise RuntimeError(
        f"Gemini is temporarily unavailable after {max_attempts} attempts. "
        f"Please try again later. Last error: {last_error}"
    )


def demo_response(prompt: str) -> str:
    if "nutrition" in prompt.lower() or "recovery" in prompt.lower():
        return (
            "Demo nutrition/recovery tip: Include a balanced meal with a protein "
            "source, vegetables or fruit, and enough fluids. Adjust food choices "
            "to your personal needs."
        )

    return """DEMO MODE – Sample 7-Day Workout Plan

Day 1 – Full Body
- Warm-up: 5–10 minutes easy movement
- Main: Squats 3x10, Push-ups 3x8, Rows 3x10, Plank 3x30 sec
- Cooldown: 5 minutes gentle stretching

Day 2 – Cardio & Core
- Warm-up: 5 minutes
- Main: Brisk walk 25 minutes, Dead bug 3x10, Plank 3x30 sec
- Cooldown: 5 minutes

Day 3 – Upper Body
- Warm-up: 5–10 minutes
- Main: Incline push-ups 3x10, Rows 3x10, Shoulder raises 2x12
- Cooldown: 5 minutes

Day 4 – Recovery
- Easy walk and gentle mobility for 20–30 minutes

Day 5 – Lower Body
- Warm-up: 5–10 minutes
- Main: Squats 3x10, Glute bridges 3x12, Lunges 2x8 each side
- Cooldown: 5 minutes

Day 6 – Full Body
- Warm-up: 5–10 minutes
- Main: Step-ups 3x10, Push-ups 3x8, Rows 3x10, Bird-dog 3x10
- Cooldown: 5 minutes

Day 7 – Rest
- Rest, hydration, sleep and light mobility as comfortable.

Note: This is demo content. Add a Gemini API key for AI-generated content."""