"""Configuration for the Multi-Modal Evidence Review system.
Reads API keys from environment variables. Never hardcode secrets."""
import os
from dataclasses import dataclass, field
from typing import Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class ModelConfig:
    provider: str = "anthropic"
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_model: str = "gpt-4o"
    google_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    google_model: str = "gemini-2.5-flash"
    max_retries: int = 3
    retry_delay: float = 2.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_api_calls: int = 0

    def get_provider(self) -> str:
        if self.provider == "anthropic" and self.anthropic_api_key:
            return "anthropic"
        if self.provider == "openai" and self.openai_api_key:
            return "openai"
        if self.provider == "google" and self.google_api_key:
            return "google"
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        if self.google_api_key:
            return "google"
        raise ValueError("No API key found. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY.")

model_config = ModelConfig()
