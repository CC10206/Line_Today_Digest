from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.article.models import Category
from app.config import settings

PROMPT_DIR = Path(__file__).parent / "prompts"


class EnrichResult(BaseModel):
    summary: str
    category: Category
    keywords: list[str] = Field(max_length=5)


class LLMClient:
    def __init__(self, client: genai.Client):
        self.client = client
        self.prompt = (PROMPT_DIR / "enrich.txt").read_text(encoding="utf-8")

    def enrich(self, title: str, content: str) -> EnrichResult:
        resp = self.client.models.generate_content(
            model=settings.chat_model,
            contents=self.prompt.format(
                categories="、".join(Category), title=title, content=content[:3000]
            ),
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=EnrichResult,
            ),
        )
        return resp.parsed

    def embed(self, text: str) -> list[float]:
        resp = self.client.models.embed_content(
            model=settings.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dimension),
        )
        return resp.embeddings[0].values


def get_llm_client() -> LLMClient:
    return LLMClient(genai.Client(api_key=settings.gemini_api_key))
