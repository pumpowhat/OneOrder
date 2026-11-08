import base64
import io
import json
from types import SimpleNamespace

import pytest
from PIL import Image

from backend.services.intake import ClaudeClient
from backend.services.intake.image import MAX_SIDE, prepare_image


class FakeMessages:
    def __init__(self, reply, stop_reason="end_turn"):
        self.reply, self.stop_reason, self.kwargs = reply, stop_reason, None

    def create(self, **kwargs):
        self.kwargs = kwargs
        block = SimpleNamespace(type="text", text=json.dumps(self.reply))
        return SimpleNamespace(content=[block], stop_reason=self.stop_reason)


def make_client(reply, stop_reason="end_turn"):
    messages = FakeMessages(reply, stop_reason)
    return ClaudeClient(client=SimpleNamespace(messages=messages), model="test-model"), messages


def png(size=(3000, 1000), mode="RGB"):
    buf = io.BytesIO()
    Image.new(mode, size, "white").save(buf, format="PNG")
    return buf.getvalue()


def test_prepare_image_downscales_and_converts_to_jpeg():
    data, media_type = prepare_image(png(mode="RGBA"))
    image = Image.open(io.BytesIO(data))
    assert media_type == "image/jpeg" and image.format == "JPEG"
    assert max(image.size) == MAX_SIDE


def test_prepare_image_applies_exif_rotation():
    buf = io.BytesIO()
    exif = Image.Exif()
    exif[0x0112] = 6  # stored sideways, display rotated 90 degrees
    Image.new("RGB", (400, 200), "white").save(buf, format="JPEG", exif=exif)
    data, _ = prepare_image(buf.getvalue())
    assert Image.open(io.BytesIO(data)).size == (200, 400)


def test_prepare_image_rejects_non_image():
    with pytest.raises(ValueError):
        prepare_image(b"not an image")


def test_extract_from_image_sends_image_and_schema():
    reply = {"customer": None, "delivery_site": None, "requested_date": None, "lines": []}
    client, messages = make_client(reply)
    assert client.extract_from_image(png(), "image/png") == reply
    kwargs = messages.kwargs
    assert kwargs["model"] == "test-model"
    assert kwargs["output_config"]["format"]["type"] == "json_schema"
    image_block = kwargs["messages"][0]["content"][0]
    assert image_block["source"]["media_type"] == "image/jpeg"
    assert Image.open(io.BytesIO(base64.b64decode(image_block["source"]["data"]))).format == "JPEG"


def test_extract_from_text_and_map_columns():
    client, messages = make_client({"description": "Navn", "quantity": "Antal"})
    assert client.map_excel_columns(["Navn", "Antal"], [["Skruer", 4]])["quantity"] == "Antal"
    assert "Skruer" in messages.kwargs["messages"][0]["content"]
    client.extract_from_text("Hej")
    assert "Hej" in messages.kwargs["messages"][0]["content"]


def test_pdf_sent_as_native_document_with_order_schema():
    from backend.services.intake.prompts import ORDER_SCHEMA
    from tests.test_pdf_intake import pdf_bytes

    data = pdf_bytes(scanned=True)
    client, messages = make_client({"lines": []})
    assert client.extract_from_pdf(data) == {"lines": []}
    document, prompt = messages.kwargs["messages"][0]["content"]
    assert document["type"] == "document"
    assert document["source"]["type"] == "base64"
    assert document["source"]["media_type"] == "application/pdf"
    assert base64.b64decode(document["source"]["data"]) == data
    assert "all pages" in prompt["text"] and "OCR" in prompt["text"]
    assert messages.kwargs["output_config"]["format"]["schema"] == ORDER_SCHEMA


@pytest.mark.parametrize("reason", ["refusal", "max_tokens"])
def test_failed_stop_reason_raises(reason):
    client, _ = make_client({}, stop_reason=reason)
    with pytest.raises(RuntimeError):
        client.extract_from_text("x")
