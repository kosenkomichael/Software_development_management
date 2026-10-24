from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.services.llm.base import AbstractLLMClient


class OpenAICompatibleClient(AbstractLLMClient):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_api_base,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def complete(
        self, system: str, user: str, file_parts: list[dict] | None = None
    ) -> str:
        content: str | list[dict] = user
        if file_parts:
            content = [*file_parts, {"type": "text", "text": user}]
        response = await self._client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            max_tokens=settings.llm_max_tokens,
        )
        return response.choices[0].message.content or ""
