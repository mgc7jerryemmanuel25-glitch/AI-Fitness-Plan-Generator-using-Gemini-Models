from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import router as api_router
from .config import get_settings
from .database import init_db
from .routes import router as html_router

settings = get_settings()

app = FastAPI(
    title=settings["app_title"],
    description="AI-powered 7-day fitness plan generator using Gemini.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(html_router)
app.include_router(api_router)


@app.on_event("startup")
def startup_event():
    init_db()
