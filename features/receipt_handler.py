from features.prompts import RECEIPT_PROMPT

from pathlib import Path

from google import genai
from google.genai import types
from schema import ReceiptData

from config import GEMINI_API_KEY, GEMINI_MODEL


class ReceiptAnalyzer:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def analyze(self, path: Path, mime_type: str) -> ReceiptData:
        data = path.read_bytes()
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                RECEIPT_PROMPT,
                types.Part.from_bytes(data=data, mime_type=mime_type),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReceiptData,
                temperature=0,
            ),
        )
        if response.parsed is not None:
            if isinstance(response.parsed, ReceiptData):
                return response.parsed
            return ReceiptData.model_validate(response.parsed)
        return ReceiptData.model_validate_json(response.text)
