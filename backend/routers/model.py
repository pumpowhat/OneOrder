from fastapi import APIRouter, HTTPException

from backend.services.eta import model_info

router = APIRouter(prefix="/api", tags=["model"])


@router.get("/model")
def get_model() -> dict:
    """Metrics, features and importance of the ETA model (for the Model screen)."""
    try:
        return model_info()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"ETA model unavailable: {exc}") from exc
