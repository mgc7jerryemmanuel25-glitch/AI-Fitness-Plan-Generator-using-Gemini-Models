# FitBuddy – AI Fitness Plan Generator

FitBuddy is a FastAPI + Jinja2 + SQLite web application based on the supplied project documentation. It accepts user fitness information, generates a 7-day workout plan with Gemini, provides a nutrition/recovery tip, stores the result in SQLite, and lets the user submit feedback to generate an updated plan.

## Architecture

Browser → FastAPI → Service layer → Gemini API
                         ↓
                    SQLAlchemy
                         ↓
                       SQLite

## Main files

- `app/main.py` – application entry point
- `app/routes.py` – HTML routes
- `app/api.py` – JSON API routes
- `app/schemas.py` – Pydantic validation
- `app/database.py` – SQLAlchemy/SQLite
- `app/models.py` – database models
- `app/gemini_generator.py` – workout generation
- `app/gemini_flash_generator.py` – nutrition/recovery tip
- `app/updated_plan.py` – feedback-based plan update
- `app/config.py` – environment configuration
- `templates/` – Jinja2 pages
- `static/` – CSS and JavaScript

## Modern Gemini integration

The supplied document describes the older `google-generativeai` package and Gemini 1.5 Pro/Flash. This implementation preserves the documented architecture and features but uses Google's newer `google-genai` SDK. Model names are configurable through `.env`, so the application does not depend on a single hard-coded model.

## Windows / VS Code setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt:

```cmd
.venv\Scriptsctivate.bat
```

Copy `.env.example` to `.env` and set your Gemini API key.

Start:

```powershell
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- `http://127.0.0.1:8000/view-all-users?token=YOUR_ADMIN_TOKEN`

## Demo mode

You can test the full UI and SQLite workflow without Gemini:

```env
DEMO_MODE=true
```

If `GOOGLE_API_KEY` is missing, the app also falls back to demo content. Set `DEMO_MODE=false` and a valid key to use Gemini.

## User flow

1. Enter name, user ID, age, weight, goal and intensity.
2. Generate the 7-day plan.
3. FitBuddy stores the user and plan in SQLite.
4. The result page shows the plan and nutrition/recovery tip.
5. Submit feedback such as "add more cardio".
6. Gemini revises the plan.
7. The revised plan is stored separately from the original.
8. The admin page shows users and both plan versions.

## API endpoints

- `GET /api/health`
- `POST /api/generate-workout`
- `POST /api/nutrition-tip`
- `POST /api/update-plan/{user_id}`
- `GET /api/users`
- `GET /api/users/{user_id}`
- `DELETE /api/users/{user_id}`

## Testing

With the virtual environment active:

```powershell
pytest -q
```

The included smoke tests verify the FastAPI home and health endpoints.

## Database

SQLite is created automatically as `fitbuddy.db`. The application uses two tables:

- `users`
- `workout_plans`

## Safety

FitBuddy provides general wellness information, not diagnosis or medical treatment. Generated plans should be reviewed by an appropriately qualified professional when necessary. The prompts tell Gemini not to diagnose injuries or medical conditions.
