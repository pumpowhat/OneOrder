"""Sample inbox: the demo emails, photos and spreadsheets in ``samples/``, importable in one call."""

import mimetypes
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.ai import get_ai_client
from backend.db import get_db
from backend.routers.intake import ingest
from backend.services.intake import AIClient, DraftOrder

router = APIRouter(prefix="/api", tags=["inbox"])

REPO_ROOT = Path(__file__).resolve().parents[2]
FOLDERS = {"emails": "email", "photos": "image", "excel": "excel", "pdf": "pdf"}
EXTENSIONS = {".txt", ".eml", ".jpg", ".jpeg", ".png", ".webp", ".xlsx", ".pdf"}


def inbox_dir() -> Path:
    return Path(os.getenv("INBOX_DIR", REPO_ROOT / "samples"))


def _preview(path: Path) -> str | None:
    """First meaningful lines of an email, so the list says what each message is about."""
    if path.suffix.lower() not in {".txt", ".eml"}:
        return None
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    return " ".join(lines[:2])[:160] or None


def _items() -> list[dict]:
    base = inbox_dir()
    items = []
    for folder, kind in FOLDERS.items():
        directory = base / folder
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                items.append(
                    {
                        "id": f"{folder}/{path.name}",
                        "kind": kind,
                        "filename": path.name,
                        "size_bytes": path.stat().st_size,
                        "preview": _preview(path),
                    }
                )
    return items


@router.get("/inbox")
def list_inbox() -> list[dict]:
    """Messages waiting in the sample inbox (emails, handwritten photos, Excel sheets)."""
    return _items()


class ImportRequest(BaseModel):
    id: str


@router.post("/inbox/import", response_model=DraftOrder)
def import_inbox_item(
    payload: ImportRequest,
    ai: AIClient = Depends(get_ai_client),
    db: Session = Depends(get_db),
) -> DraftOrder:
    """Process one inbox item exactly like an upload and return the new draft order.

    Only ids returned by ``GET /api/inbox`` are accepted, so the path cannot leave the inbox folder.
    """
    if payload.id not in {item["id"] for item in _items()}:
        raise HTTPException(status_code=404, detail=f"Inbox item '{payload.id}' not found")
    path = inbox_dir() / payload.id
    return ingest(
        db,
        ai,
        filename=path.name,
        content=path.read_bytes(),
        mime=mimetypes.guess_type(path.name)[0],
    )
