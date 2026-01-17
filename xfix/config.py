"""Configuration loading from .env file."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration."""

    # ClipJot API
    clipjot_api_url: str
    clipjot_api_token: str

    # Ollama
    ollama_model: str
    ollama_host: str

    # Tweet fetch delays (seconds) - for fxtwitter/oEmbed APIs
    fetch_min_delay: float
    fetch_max_delay: float
    fetch_max_backoff: float

    # State
    state_file: Path

    # Logging
    log_level: str
    log_verbose: bool


def load_config(env_file: Path | None = None) -> Config:
    """
    Load configuration from environment variables.

    Args:
        env_file: Optional path to .env file. Defaults to .env in current directory.

    Returns:
        Config object with all settings.

    Raises:
        ValueError: If required configuration is missing.
    """
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    # Required settings
    api_url = os.getenv("CLIPJOT_API_URL")
    api_token = os.getenv("CLIPJOT_API_TOKEN")

    if not api_url:
        raise ValueError("CLIPJOT_API_URL is required")
    if not api_token:
        raise ValueError("CLIPJOT_API_TOKEN is required")

    # Optional settings with defaults
    return Config(
        clipjot_api_url=api_url.rstrip("/"),
        clipjot_api_token=api_token,
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen3"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        fetch_min_delay=float(os.getenv("FETCH_MIN_DELAY", "1")),
        fetch_max_delay=float(os.getenv("FETCH_MAX_DELAY", "3")),
        fetch_max_backoff=float(os.getenv("FETCH_MAX_BACKOFF", "300")),
        state_file=Path(os.getenv("STATE_FILE", "state.json")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_verbose=os.getenv("LOG_VERBOSE", "true").lower() == "true",
    )
