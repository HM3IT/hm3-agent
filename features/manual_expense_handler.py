from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL
from features.prompts import MANUAL_EXPENSE_PROMPT
from schema import ManualExpenseResult


class ManualExpenseAnalyzer:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def analyze(self, message_text: str) -> ManualExpenseResult:
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                MANUAL_EXPENSE_PROMPT,
                f"User message:\n{message_text}",
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ManualExpenseResult,
                temperature=0,
            ),
        )

        if response.parsed is not None:
            if isinstance(response.parsed, ManualExpenseResult):
                return response.parsed

            return ManualExpenseResult.model_validate(
                response.parsed
            )

        return ManualExpenseResult.model_validate_json(
            response.text
        )