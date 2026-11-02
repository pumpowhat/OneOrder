from typing import Protocol


class AIClient(Protocol):
    """What intake needs from an AI provider; live and demo clients implement this."""

    def extract_from_image(self, data: bytes, media_type: str) -> dict:
        """Read a photo of a material list.

        Returns {"customer", "delivery_site", "requested_date", "lines": [
        {"description", "quantity", "unit", "confidence", "source_text"}]}.
        """

    def extract_from_text(self, text: str) -> dict:
        """Read a free-text order email. Same return shape as extract_from_image."""

    def map_excel_columns(self, headers: list[str], sample_rows: list[list]) -> dict:
        """Map a customer's own column layout.

        Returns {"description": <header>, "quantity": <header>, "unit": <header or None>,
        "customer", "delivery_site", "requested_date"}; the last three are optional.
        """
