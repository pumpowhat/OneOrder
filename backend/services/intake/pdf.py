"""Validate PDFs before sending the whole document to a provider's native vision OCR."""

import io

from pypdf import PdfReader

MAX_PDF_PAGES = 20


def validate_pdf(data: bytes) -> None:
    if not data.startswith(b"%PDF-"):
        raise ValueError("Not a readable PDF")
    try:
        reader = PdfReader(io.BytesIO(data), strict=True)
        encrypted = reader.is_encrypted
        pages = 0 if encrypted else len(reader.pages)
    except Exception as exc:  # malformed documents must not reach the provider or expose parser errors
        raise ValueError("Not a readable PDF; the file may be damaged") from exc
    if encrypted:
        raise ValueError("Password-protected or encrypted PDFs are not supported; upload an unencrypted copy")
    if not pages:
        raise ValueError("PDF has no pages")
    if pages > MAX_PDF_PAGES:
        raise ValueError(f"PDF is limited to {MAX_PDF_PAGES} pages; split the document before uploading")
