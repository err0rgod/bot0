import logging
from typing import Optional

logger = logging.getLogger("LLMClient")

class LLMClient:
    def __init__(self, provider: str = "deepseek"):
        """
        Initializes the LLM client with the specified provider.
        """
        self.provider = provider.lower()
        self.client = None
        
        if self.provider == "deepseek":
            from .deepseek_client import DeepSeekClient
            self.client = DeepSeekClient()
            logger.info("Initialized DeepSeekClient.")
        elif self.provider == "openrouter":
            # Placeholder for future providers
            logger.info("OpenRouter provider initialized (placeholder).")
            # from .openrouter_client import OpenRouterClient
            # self.client = OpenRouterClient()
            raise NotImplementedError("OpenRouter provider is not yet implemented.")
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    async def generate(self, messages: list, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 1500) -> str:
        """
        Routes the text generation request to the selected provider.
        """
        if self.provider == "deepseek":
            # Use default model if none specified
            use_model = model if model else "deepseek-chat"
            return await self.client.generate(
                messages=messages, 
                model=use_model, 
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            raise NotImplementedError(f"Generate method not implemented for provider {self.provider}")
