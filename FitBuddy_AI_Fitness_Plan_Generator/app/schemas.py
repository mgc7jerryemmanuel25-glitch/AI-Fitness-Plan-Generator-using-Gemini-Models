from pydantic import BaseModel, Field, field_validator


class UserInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    user_id: str = Field(min_length=1, max_length=50)
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=20, le=500)
    goal: str = Field(min_length=2, max_length=100)
    intensity: str = Field(min_length=3, max_length=20)

    @field_validator("name", "goal", "user_id")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty")
        return value

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"low", "medium", "high"}:
            raise ValueError("Intensity must be low, medium, or high")
        return value


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=50)
    feedback: str = Field(min_length=3, max_length=2000)


class NutritionRequest(BaseModel):
    goal: str = Field(min_length=2, max_length=100)
