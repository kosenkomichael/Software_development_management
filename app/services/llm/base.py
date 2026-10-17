from abc import ABC, abstractmethod


class AbstractLLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str) -> str:
        """Send a prompt and return the text response."""
