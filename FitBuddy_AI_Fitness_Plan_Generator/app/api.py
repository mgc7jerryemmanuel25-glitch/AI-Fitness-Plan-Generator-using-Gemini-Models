from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .gemini_generator import generate_workout_gemini
from .models import User, WorkoutPlan
from .schemas import FeedbackRequest, NutritionRequest, UserInput
from .updated_plan import update_workout_plan

router = APIRouter(prefix="/api", tags=["FitBuddy API"])


@router.get("/health")
def api_health():
    return {"status": "ok", "service": "FitBuddy"}


@router.post("/generate-workout")
def api_generate_workout(payload: UserInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == payload.user_id))

    if user is None:
        user = User(**payload.model_dump())
        db.add(user)
    else:
        for field, value in payload.model_dump().items():
            setattr(user, field, value)

    try:
        workout = generate_workout_gemini(payload.model_dump())
        tip = generate_nutrition_tip_with_flash(payload.goal)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"AI generation failed: {exc}") from exc

    plan = db.scalar(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == payload.user_id)
        .order_by(WorkoutPlan.id.desc())
    )

    if plan is None:
        plan = WorkoutPlan(
            user_id=payload.user_id,
            original_plan=workout,
            nutrition_tip=tip,
        )
        db.add(plan)
    else:
        plan.original_plan = workout
        plan.updated_plan = None
        plan.feedback = None
        plan.nutrition_tip = tip
        plan.updated_at = None

    db.commit()
    db.refresh(user)
    db.refresh(plan)

    return {
        "message": "Workout plan generated and saved successfully.",
        "user": {
            "user_id": user.user_id, "name": user.name, "age": user.age,
            "weight": user.weight, "goal": user.goal, "intensity": user.intensity,
        },
        "plan": {
            "original_plan": plan.original_plan,
            "updated_plan": plan.updated_plan,
            "nutrition_tip": plan.nutrition_tip,
        },
    }


@router.post("/nutrition-tip")
def api_nutrition_tip(payload: NutritionRequest):
    try:
        return {
            "goal": payload.goal,
            "nutrition_tip": generate_nutrition_tip_with_flash(payload.goal),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {exc}") from exc


@router.post("/update-plan/{user_id}")
def api_update_plan(user_id: str, payload: FeedbackRequest, db: Session = Depends(get_db)):
    if payload.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch.")

    user = db.scalar(select(User).where(User.user_id == user_id))
    plan = db.scalar(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user_id)
        .order_by(WorkoutPlan.id.desc())
    )

    if not user or not plan:
        raise HTTPException(status_code=404, detail="User or plan not found.")

    source_plan = plan.updated_plan or plan.original_plan

    try:
        plan.updated_plan = update_workout_plan(source_plan, payload.feedback)
        plan.feedback = payload.feedback
        plan.updated_at = datetime.now(timezone.utc)
        plan.nutrition_tip = generate_nutrition_tip_with_flash(user.goal)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"AI update failed: {exc}") from exc

    db.commit()
    db.refresh(plan)

    return {
        "message": "Workout plan updated successfully.",
        "user_id": user_id,
        "updated_plan": plan.updated_plan,
        "nutrition_tip": plan.nutrition_tip,
    }


@router.get("/users")
def api_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.id.desc())).all()
    return [
        {
            "user_id": user.user_id, "name": user.name, "age": user.age,
            "weight": user.weight, "goal": user.goal, "intensity": user.intensity,
        }
        for user in users
    ]


@router.get("/users/{user_id}")
def api_user(user_id: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == user_id))
    plan = db.scalar(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user_id)
        .order_by(WorkoutPlan.id.desc())
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    return {
        "user": {
            "user_id": user.user_id, "name": user.name, "age": user.age,
            "weight": user.weight, "goal": user.goal, "intensity": user.intensity,
        },
        "plan": None if not plan else {
            "original_plan": plan.original_plan,
            "updated_plan": plan.updated_plan,
            "nutrition_tip": plan.nutrition_tip,
            "feedback": plan.feedback,
        },
    }


@router.delete("/users/{user_id}")
def api_delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully."}
