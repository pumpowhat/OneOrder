from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from backend.ai import ai_mode  # noqa: E402  (after load_dotenv so AI_MODE is read from .env)
from backend.routers import intake  # noqa: E402

app = FastAPI(title="OneOrder", version="0.1.0")
app.include_router(intake.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "ai_mode": ai_mode()}
