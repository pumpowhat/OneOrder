import logging
import mimetypes

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.ai import get_ai_client
from backend.db import get_db, save_draft_order
from backend.services.intake import AIClient, DraftOrder, IntakeService, UnsupportedInput
from backend.services.intake.demo_client import DemoFixtureMissing
from backend.services.matching import CatalogueMatcher, load_catalog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def ingest(
    db: Session,
    ai: AIClient,
    *,
    filename: str | None = None,
    content: bytes | None = None,
    text: str | None = None,
    mime: str | None = None,
) -> DraftOrder:
    """Read one input (file bytes or pasted text), match it to the catalogue and store the draft.

    Shared by POST /api/intake and the sample inbox so both follow the same path. Raises
    HTTPException with the status the API documents.
    """
    service = IntakeService(ai)
    source: tuple[bytes, str] | None = None
    try:
        if content is not None:
            if len(content) > MAX_UPLOAD_BYTES:
                raise HTTPException(413, "File is larger than 10 MB")
            order = service.process(filename or "", content)
            known = mime if mime and mime != "application/octet-stream" else None
            if order.source_type == "pdf":
                known = "application/pdf"  # validated content; never serve a PDF as a caller-supplied HTML MIME
            source = (content, known or mimetypes.guess_type(filename or "")[0] or "application/octet-stream")
        else:
            order = service.from_email(text or "")
            source = ((text or "").encode("utf-8"), "text/plain")
    except (UnsupportedInput, DemoFixtureMissing, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc

    # Match order lines against catalogue; catch only expected missing/malformed catalogue errors
    try:
        catalog = load_catalog()
        matcher = CatalogueMatcher(catalog, ai=ai)
        order = matcher.match_order(order)
    except (FileNotFoundError, ValueError) as exc:
        logger.warning("Catalogue matching skipped: %s", exc)
        order.warnings.append(f"Catalogue matching skipped: {exc}")

    save_draft_order(db, order, source=source)
    return order


@router.post("/intake", response_model=DraftOrder)
async def intake(
    file: UploadFile | None = File(None, description="Photo (.jpg/.png/.webp), PDF (.pdf, up to 20 pages), Excel (.xlsx) or email (.txt/.eml); max 10 MB"),
    text: str | None = Form(None, description="Pasted email text, instead of a file"),
    ai: AIClient = Depends(get_ai_client),
    db: Session = Depends(get_db),
) -> DraftOrder:
    if (file is None) == (text is None):
        raise HTTPException(422, "Send either a file or text, not both or neither")
    if file is not None:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        return ingest(db, ai, filename=file.filename, content=content, mime=file.content_type)
    return ingest(db, ai, text=text)
