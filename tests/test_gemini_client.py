import io
import json
from types import SimpleNamespace

from PIL import Image
from google.genai import errors
import pytest

from backend.ai import ai_provider, make_live_client
from backend.services.intake import ClaudeClient, GeminiClient
from backend.services.intake.gemini_client import DEFAULT_MODEL
from backend.services.intake.prompts import COLUMN_SCHEMA, MATCH_SCHEMA, ORDER_RULES, ORDER_SCHEMA


class FakeModels:
    def __init__(self, text, finish="STOP"):
        self.text, self.finish, self.kwargs = text, finish, None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        candidate = SimpleNamespace(finish_reason=SimpleNamespace(name=self.finish))
        return SimpleNamespace(text=self.text, candidates=[candidate])


def make_client(reply, finish="STOP", text=None):
    models = FakeModels(json.dumps(reply) if text is None else text, finish)
    return GeminiClient(client=SimpleNamespace(models=models), model="test-model"), models


def png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (400, 200), "white").save(buf, format="PNG")
    return buf.getvalue()


def test_extract_from_image_sends_jpeg_part_and_schema():
    reply = {"customer": "Acme", "delivery_site": None, "requested_date": None, "lines": []}
    client, models = make_client(reply)
    assert client.extract_from_image(png(), "image/png") == reply

    kwargs = models.kwargs
    assert kwargs["model"] == "test-model"
    image_part, prompt = kwargs["contents"]
    assert image_part.inline_data.mime_type == "image/jpeg"
    assert image_part.inline_data.data[:2] == b"\xff\xd8"  # prepare_image re-encodes to JPEG
    assert prompt == "Extract the order from this photo."
    config = kwargs["config"]
    assert config.system_instruction == ORDER_RULES
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema == ORDER_SCHEMA


def test_extract_from_text_and_map_columns_and_match_product():
    client, models = make_client({"customer": None, "delivery_site": None, "requested_date": None, "lines": []})
    client.extract_from_text("Hej, 40 stk gips")
    assert "40 stk gips" in models.kwargs["contents"]

    client, models = make_client(
        {"description": "Beskrivelse", "quantity": "Antal", "unit": None, "customer": None,
         "delivery_site": None, "requested_date": None}
    )
    assert client.map_excel_columns(["Beskrivelse", "Antal"], [["Gips", 3]])["quantity"] == "Antal"
    assert models.kwargs["config"].response_json_schema == COLUMN_SCHEMA
    assert "Beskrivelse" in models.kwargs["contents"]

    client, models = make_client({"sku": "GYP-13-2400"})
    assert client.match_product("gips", [{"sku": "GYP-13-2400"}]) == "GYP-13-2400"
    assert models.kwargs["config"].response_json_schema == MATCH_SCHEMA


@pytest.mark.parametrize("finish", ["MAX_TOKENS", "SAFETY", "RECITATION"])
def test_non_stop_finish_reason_raises(finish):
    client, _ = make_client({"sku": None}, finish=finish)
    with pytest.raises(RuntimeError, match=finish):
        client.match_product("x", [])


def test_empty_response_raises():
    client, _ = make_client(None, text="")
    with pytest.raises(RuntimeError, match="AI extraction failed"):
        client.extract_from_text("x")


def test_model_comes_from_argument_env_or_default(monkeypatch):
    fake = SimpleNamespace(models=FakeModels("{}"))
    monkeypatch.delenv("AI_MODEL", raising=False)
    assert GeminiClient(client=fake).model == DEFAULT_MODEL
    monkeypatch.setenv("AI_MODEL", "from-env")
    assert GeminiClient(client=fake).model == "from-env"
    assert GeminiClient(client=fake, model="explicit").model == "explicit"


# --- Provider selection ------------------------------------------------------------------------------


def test_provider_defaults_to_gemini(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    assert ai_provider() == "gemini"


@pytest.mark.parametrize(("name", "cls"), [("gemini", GeminiClient), ("Claude", ClaudeClient)])
def test_make_live_client_builds_chosen_provider(monkeypatch, name, cls):
    monkeypatch.setenv("AI_PROVIDER", name)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert isinstance(make_live_client(), cls)


def test_unknown_provider_is_an_error(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    with pytest.raises(ValueError, match="Unknown AI_PROVIDER 'openai'"):
        ai_provider()


# --- API errors become readable RuntimeErrors (the router answers 502) ---------------------------------


class RaisingModels:
    def __init__(self, exc):
        self.exc = exc

    def generate_content(self, **kwargs):
        raise self.exc


def raising_client(code, status, message="boom"):
    exc = errors.APIError(code, {"error": {"code": code, "status": status, "message": message}})
    return GeminiClient(client=SimpleNamespace(models=RaisingModels(exc)), model="m1")


@pytest.mark.parametrize(
    ("code", "status", "expected"),
    [
        (429, "RESOURCE_EXHAUSTED", "quota exceeded for model 'm1'"),
        (404, "NOT_FOUND", "model 'm1' is not available"),
        (403, "PERMISSION_DENIED", "check GEMINI_API_KEY"),
        (503, "UNAVAILABLE", "Gemini API error 503 UNAVAILABLE: boom"),
    ],
)
def test_api_errors_are_described(code, status, expected):
    with pytest.raises(RuntimeError) as info:
        raising_client(code, status).extract_from_text("x")
    assert expected in str(info.value)


def test_quota_errors_are_not_retried():
    from backend.services.intake.gemini_client import RETRY_STATUS_CODES

    assert 429 not in RETRY_STATUS_CODES and 503 in RETRY_STATUS_CODES
