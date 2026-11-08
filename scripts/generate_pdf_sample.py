"""Wrap the existing DK photo in a scan-only PDF and reuse its reviewed demo truth.

    python -m scripts.generate_pdf_sample
"""

import io
import json
from pathlib import Path

from PIL import Image

from backend.services.intake.demo_client import fixture_key


def main() -> None:
    samples = Path(__file__).resolve().parents[1] / "samples"
    photo = samples / "photos/dk-handwritten-1.jpg"
    out = io.BytesIO()
    with Image.open(photo) as image:
        image.convert("RGB").save(
            out, format="PDF", resolution=150,
            creationDate="D:20261108000000Z", modDate="D:20261108000000Z",
        )
    data = out.getvalue()
    target = samples / "pdf/dk-scan.pdf"
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(data)

    fixture = json.loads((samples / f"fixtures/{fixture_key(photo.read_bytes())}.json").read_text("utf-8"))
    fixture["source"] = target.name
    (samples / f"fixtures/{fixture_key(data)}.json").write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", "utf-8",
    )
    expected = json.loads((samples / "expected/dk-handwritten-1.jpg.json").read_text("utf-8"))
    expected["source_file"] = target.name
    (samples / "expected/dk-scan.pdf.json").write_text(
        json.dumps(expected, ensure_ascii=False, indent=2) + "\n", "utf-8",
    )
    print(f"Created {target} with {expected['line_count']} material lines (image-only PDF).")


if __name__ == "__main__":
    main()
