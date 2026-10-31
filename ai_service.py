
import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors


load_dotenv()

MODEL_NAME = "gemini-3.8-flash"


class AIServiceError(Exception):
    """Raised when the AI service cannot complete a request."""


def generate_json(prompt, max_attempts=3):
    """Generate JSON using Gemini, retrying temporary failures."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise AIServiceError(
            "GEMINI_API_KEY was not found. Check your .env file."
        )

    if not isinstance(prompt, str) or not prompt.strip():
        raise AIServiceError("The AI prompt cannot be empty.")

    client = genai.Client(api_key=api_key)
    last_error = None

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            )

            response_text = getattr(response, "text", None)

            if not response_text:
                raise AIServiceError(
                    "Gemini returned an empty response. Please try again."
                )

            try:
                return json.loads(response_text)
            except json.JSONDecodeError as exc:
                raise AIServiceError(
                    "Gemini returned invalid JSON. Please try again."
                ) from exc

        except AIServiceError:
            raise

        except Exception as exc:
            last_error = exc
            error_text = str(exc).lower()
            status_code = getattr(exc, "code", None)

            # Retry temporary overload, rate limits and server errors.
            temporary_error = (
                status_code in (429, 500, 502, 503, 504)
                or any(term in error_text for term in (
                    "resource_exhausted",
                    "too many requests",
                    "rate limit",
                    "high demand",
                    "overloaded",
                    "temporarily unavailable",
                    "internal server error",
                    "503",
                    "429",
                ))
            )

            if not temporary_error or attempt == max_attempts - 1:
                break

            time.sleep(2 ** (attempt + 1))

    error_text = str(last_error).lower() if last_error else ""

    if any(term in error_text for term in (
        "resource_exhausted",
        "too many requests",
        "rate limit",
        "429",
        "quota",
    )):
        raise AIServiceError(
            "Gemini rate limit or quota reached. Check your API usage "
            "and limits, wait before retrying, and try again."
        ) from last_error

    if any(term in error_text for term in (
        "high demand",
        "overloaded",
        "503",
        "temporarily unavailable",
    )):
        raise AIServiceError(
            "Gemini is temporarily overloaded. Please wait a minute "
            "and try again."
        ) from last_error

    raise AIServiceError(
        f"Gemini request failed: {last_error}. Check your API key, "
        "model configuration, internet connection and API access."
    ) from last_error
