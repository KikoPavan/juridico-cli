"""
Gemini client adapter compatible with MarkItDown's LLM interface.
Ported from devops/markdown/src/genai_adapter.py.
"""

import base64
import io

from google import genai
from google.genai.types import (
    GenerateContentConfig,
    HarmBlockThreshold,
    HarmCategory,
    SafetySetting,
)
from PIL import Image


class _MockChoice:
    def __init__(self, content: str) -> None:
        self.message = type("obj", (object,), {"content": content})()


class _MockResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_MockChoice(content)]


class GeminiClientAdapter:
    """
    Wraps google-genai to look like an OpenAI client,
    so MarkItDown can use Gemini as its LLM backend.
    """

    def __init__(self, api_key: str, model_name: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.client_models = self.client.models
        self.model_name = model_name
        self.chat = self
        self.completions = self

    def create(self, model: str, messages: list, **kwargs) -> _MockResponse:
        prompt = ""
        image_url = ""
        for part in messages[0]["content"]:
            if part["type"] == "text":
                prompt = part["text"]
            elif part["type"] == "image_url":
                image_url = part["image_url"]["url"]

        header, encoded = image_url.split(",", 1)
        image_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_data))

        safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
        ]

        config = GenerateContentConfig(safety_settings=safety_settings)

        response = self.client_models.generate_content(
            model=f"models/{self.model_name}",
            contents=[prompt, image],
            config=config,
        )

        text_result = ""
        try:
            text_result = response.text
        except AttributeError:
            if (
                response.candidates
                and response.candidates[0].content is not None
                and response.candidates[0].content.parts
            ):
                text_result = response.candidates[0].content.parts[0].text

        return _MockResponse(content=text_result)
