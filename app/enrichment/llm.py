from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field

from app.article.models import Category
from app.config import settings

PROMPT_DIR = Path(__file__).parent / "prompts"


class EnrichResult(BaseModel):
    summary: str
    category: Category
    keywords: list[str] = Field(max_length=5)


class LLMClient:
    def __init__(self, client: OpenAI):
        self.client = client
        self.prompt = (PROMPT_DIR / "enrich.txt").read_text(encoding="utf-8")

    def enrich(self, title: str, content: str) -> EnrichResult:
        resp = self.client.beta.chat.completions.parse(
            model=settings.chat_model,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": self.prompt.format(
                        categories="、".join(Category), title=title, content=content[:3000]
                    ),
                }
            ],
            response_format=EnrichResult,
        )
        return resp.choices[0].message.parsed

    def embed(self, text: str) -> list[float]:
        return self.client.embeddings.create(
            model=settings.embedding_model, input=text
        ).data[0].embedding
