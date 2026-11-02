import os
from functools import lru_cache
from pathlib import Path

from backend.services.intake import AIClient, ClaudeClient
from backend.services.intake.demo_client import DemoClient

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "samples" / "fixtures"


def ai_mode() -> str:
    return "live" if os.getenv("AI_MODE", "demo").lower() == "live" else "demo"


@lru_cache
def get_ai_client() -> AIClient:
    return ClaudeClient() if ai_mode() == "live" else DemoClient(FIXTURE_DIR)
