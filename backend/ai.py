import os
from functools import lru_cache
from pathlib import Path

from backend.services.intake import AIClient, ClaudeClient, GeminiClient
from backend.services.intake.demo_client import DemoClient

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "samples" / "fixtures"
PROVIDERS = {"claude": ClaudeClient, "gemini": GeminiClient}
DEFAULT_PROVIDER = "gemini"


def ai_mode() -> str:
    return "live" if os.getenv("AI_MODE", "demo").lower() == "live" else "demo"


def ai_provider() -> str:
    """Live provider chosen by AI_PROVIDER (claude | gemini); unknown values are an error, not a silent default."""
    name = os.getenv("AI_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    if name not in PROVIDERS:
        raise ValueError(f"Unknown AI_PROVIDER '{name}'; use one of: {', '.join(PROVIDERS)}")
    return name


def make_live_client() -> AIClient:
    return PROVIDERS[ai_provider()]()


@lru_cache
def get_ai_client() -> AIClient:
    return make_live_client() if ai_mode() == "live" else DemoClient(FIXTURE_DIR)
