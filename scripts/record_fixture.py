"""Record a live Claude result as a demo fixture, so demo mode can replay it without a key.

    python -m scripts.record_fixture samples/handwritten-1.jpg
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from backend.ai import FIXTURE_DIR
from backend.services.intake import ClaudeClient
from backend.services.intake.demo_client import fixture_key
from backend.services.intake.service import IMAGE_TYPES, TEXT_SUFFIXES


def main(path: Path) -> None:
    load_dotenv()
    suffix = path.suffix.lower()
    client = ClaudeClient()
    if suffix in IMAGE_TYPES:
        content = path.read_bytes()
        payload = client.extract_from_image(content, IMAGE_TYPES[suffix])
    elif suffix in TEXT_SUFFIXES:
        content = path.read_text("utf-8")
        payload = client.extract_from_text(content)
    else:
        sys.exit(f"Only photos and email text can be recorded (got {suffix}); Excel needs no fixture.")

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    target = FIXTURE_DIR / f"{fixture_key(content)}.json"
    target.write_text(json.dumps({"source": path.name, "payload": payload}, indent=2, ensure_ascii=False) + "\n", "utf-8")
    print(f"Recorded {len(payload['lines'])} lines -> {target}")
    print("Review the file by hand before committing: it is what the demo will show.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
