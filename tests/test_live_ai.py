"""Reads the sample photos with the real AI provider and compares with what is written on them.

Skipped unless you opt in, so CI and normal runs never spend API calls:

    RUN_LIVE_AI=1 AI_PROVIDER=gemini GEMINI_API_KEY=... python -m pytest tests/test_live_ai.py -s

The expected values are the payloads in samples/fixtures/, which `scripts/generate_samples.py`
writes from the same text it draws on each photo. Units are only printed, not asserted: handwriting
models sometimes read "sæk" as "stk", which the matcher does not depend on.
"""

import hashlib
import json
import os
from pathlib import Path

import pytest

from backend.ai import make_live_client

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
PHOTOS = sorted((SAMPLES / "photos").glob("*.jpg"))

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_AI") != "1", reason="live AI test: set RUN_LIVE_AI=1 (and a provider key) to run"
)


@pytest.fixture(scope="module")
def client():
    return make_live_client()


@pytest.mark.parametrize("photo", PHOTOS, ids=lambda p: p.name)
def test_photo_is_read_correctly(client, photo):
    data = photo.read_bytes()
    truth = json.loads((SAMPLES / "fixtures" / f"{hashlib.sha256(data).hexdigest()}.json").read_text("utf-8"))["payload"]

    got = client.extract_from_image(data, "image/jpeg")

    print(f"\n{photo.name}: units read {[l['unit'] for l in got['lines']]} vs {[l['unit'] for l in truth['lines']]}; "
          f"confidence {[l['confidence'] for l in got['lines']]}")
    assert got["customer"] == truth["customer"]
    assert got["delivery_site"] == truth["delivery_site"]
    assert got["requested_date"] == truth["requested_date"]
    assert [round(l["quantity"], 2) for l in got["lines"]] == [round(l["quantity"], 2) for l in truth["lines"]]
    assert all(0 <= l["confidence"] <= 1 for l in got["lines"])
