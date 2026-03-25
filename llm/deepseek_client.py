import os
import time
import logging
from openai import OpenAI

# Configure basic logging for the LLM module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DeepSeekClient")

class DeepSeekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set in the environment or .env file.")
        
        # Initialize OpenAI compatible client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
    
    def generate(self, messages: list, model: str = "deepseek-chat", temperature: float = 0.7, max_tokens: int = 1500) -> str:
        """
        Generates text using the DeepSeek API with retry and timeout logic.
        """
        max_retries = 3
        base_delay = 2.0
        timeout = 60.0  # 60 seconds request timeout

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt}/{max_retries}: Sending request to DeepSeek API ({model}).")
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
                
                elapsed = time.time() - start_time
                text = response.choices[0].message.content.strip()
                logger.info(f"Successfully generated response in {elapsed:.2f}s on attempt {attempt}.")
                
                return text

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    logger.error("Max retries reached. Failing request.")
                    raise
                
                # Exponential backoff
                time.sleep(base_delay ** attempt)
