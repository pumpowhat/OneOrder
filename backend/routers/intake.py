from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.ai import get_ai_client
from backend.services.intake import AIClient, DraftOrder, IntakeService, UnsupportedInput
from backend.services.intake.demo_client import DemoFixtureMissing

router = APIRouter(prefix="/api")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/intake", response_model=DraftOrder)
async def intake(
    file: UploadFile | None = File(None, description="Photo (.jpg/.png/.webp), Excel (.xlsx) or email (.txt/.eml)"),
    text: str | None = Form(None, description="Pasted email text, instead of a file"),
    ai: AIClient = Depends(get_ai_client),
) -> DraftOrder:
    if (file is None) == (text is None):
        raise HTTPException(422, "Send either a file or text, not both or neither")

    service = IntakeService(ai)
    try:
        if file is not None:
            content = await file.read(MAX_UPLOAD_BYTES + 1)
            if len(content) > MAX_UPLOAD_BYTES:
                raise HTTPException(413, "File is larger than 10 MB")
            return service.process(file.filename or "", content)
        return service.from_email(text)
    except (UnsupportedInput, DemoFixtureMissing, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc
