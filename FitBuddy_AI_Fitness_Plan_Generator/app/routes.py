from datetime import datetime, timezone

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import SessionLocal
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .gemini_generator import generate_workout_gemini
from .models import User, WorkoutPlan
from .schemas import UserInput
from .updated_plan import update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _get_user_and_plan(db: Session, user_id: str):
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        return None, None
    plan = db.scalar(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user_id)
        .order_by(WorkoutPlan.id.desc())
    )
    return user, plan


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": get_settings()["app_title"]},
    )


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
):
    try:
        data = UserInput(
            name=username, user_id=user_id, age=age, weight=weight,
            goal=goal, intensity=intensity
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request=request, name="index.html",
            context={"error": str(exc), "title": get_settings()["app_title"]},
            status_code=422,
        )

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.user_id == data.user_id))
        if user is None:
            user = User(**data.model_dump())
            db.add(user)
        else:
            for field, value in data.model_dump().items():
                setattr(user, field, value)

        workout_plan = generate_workout_gemini(data.model_dump())
        nutrition_tip = generate_nutrition_tip_with_flash(data.goal)

        plan = db.scalar(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == data.user_id)
            .order_by(WorkoutPlan.id.desc())
        )
        if plan is None:
            plan = WorkoutPlan(
                user_id=data.user_id,
                original_plan=workout_plan,
                nutrition_tip=nutrition_tip,
            )
            db.add(plan)
        else:
            plan.original_plan = workout_plan
            plan.updated_plan = None
            plan.feedback = None
            plan.nutrition_tip = nutrition_tip
            plan.updated_at = None

        db.commit()
        db.refresh(user)
        db.refresh(plan)

        return templates.TemplateResponse(
            request=request, name="result.html",
            context={"title": "Your FitBuddy Plan", "user": user, "plan": plan, "message": None},
        )
    except Exception as exc:
        db.rollback()
        return templates.TemplateResponse(
            request=request, name="index.html",
            context={"error": f"Could not generate the plan: {exc}", "title": get_settings()["app_title"]},
            status_code=500,
        )
    finally:
        db.close()


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(request: Request, user_id: str = Form(...), feedback: str = Form(...)):
    db = SessionLocal()
    try:
        user, plan = _get_user_and_plan(db, user_id)
        if not user or not plan:
            raise HTTPException(status_code=404, detail="User or plan not found.")

        feedback = feedback.strip()
        if len(feedback) < 3 or len(feedback) > 2000:
            raise HTTPException(status_code=422, detail="Feedback must be 3–2000 characters.")

        source_plan = plan.updated_plan or plan.original_plan
        plan.updated_plan = update_workout_plan(source_plan, feedback)
        plan.feedback = feedback
        plan.updated_at = datetime.now(timezone.utc)
        plan.nutrition_tip = generate_nutrition_tip_with_flash(user.goal)

        db.commit()
        db.refresh(plan)

        return templates.TemplateResponse(
            request=request, name="result.html",
            context={
                "title": "Updated FitBuddy Plan",
                "user": user,
                "plan": plan,
                "message": "Your plan has been updated based on your feedback.",
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not update plan: {exc}") from exc
    finally:
        db.close()


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, token: str = ""):
    settings = get_settings()
    if token != settings["admin_token"]:
        return templates.TemplateResponse(
            request=request, name="all_users.html",
            context={"users": [], "error": "Invalid admin token.", "title": "Admin"},
            status_code=401,
        )

    db = SessionLocal()
    try:
        users = db.scalars(select(User).order_by(User.id.desc())).all()
        records = []
        for user in users:
            plan = db.scalar(
                select(WorkoutPlan)
                .where(WorkoutPlan.user_id == user.user_id)
                .order_by(WorkoutPlan.id.desc())
            )
            records.append({"user": user, "plan": plan})

        return templates.TemplateResponse(
            request=request, name="all_users.html",
            context={"users": records, "error": None, "title": "All Users"},
        )
    finally:
        db.close()


@router.get("/health", response_class=HTMLResponse)
def health_page():
    return HTMLResponse("FitBuddy is running.")
