import io

from PIL import Image, ImageOps

# Longest side sent to the vision model; larger photos are only downscaled by the API anyway.
MAX_SIDE = 1568
JPEG_QUALITY = 90


def prepare_image(data: bytes) -> tuple[bytes, str]:
    """Normalise a phone photo for OCR: upright, RGB, bounded size, JPEG.

    Returns (jpeg_bytes, media_type). Raises ValueError if the bytes are not an image.
    """
    try:
        image = Image.open(io.BytesIO(data))
        image = ImageOps.exif_transpose(image)  # phone photos are often stored rotated
        image = ImageOps.autocontrast(image.convert("RGB"), cutoff=1)  # help faint pencil/pen
    except Exception as exc:
        raise ValueError("Not a readable image") from exc

    image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=JPEG_QUALITY)
    return out.getvalue(), "image/jpeg"
