from abc import ABC, abstractmethod


class AbstractLLMClient(ABC):
    @abstractmethod
    async def complete(
        self, system: str, user: str, file_parts: list[dict] | None = None
    ) -> str:
        """Send a prompt and return the text response."""
