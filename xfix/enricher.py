"""Ollama integration for AI-powered tweet summarization."""

import re
from dataclasses import dataclass

import ollama
from ollama import ResponseError

from fetcher import TweetContent


@dataclass
class EnrichmentResult:
    """Result of AI enrichment."""

    success: bool
    title: str | None = None
    comment: str | None = None
    error_message: str | None = None


# Prompt template for tweet summarization
PROMPT_TEMPLATE = """Given the following tweet content, generate:
1. A brief one-sentence title (max 100 characters) that captures the main topic
2. A 3-5 sentence summary of the content

Tweet by @{author}:
{text}

Respond in this exact format:
TITLE: <your title here>
SUMMARY: <your summary here>"""

# Patterns to parse response
TITLE_PATTERN = re.compile(r"TITLE:\s*(.+?)(?:\n|$)", re.IGNORECASE)
SUMMARY_PATTERN = re.compile(r"SUMMARY:\s*(.+)", re.IGNORECASE | re.DOTALL)


def parse_response(response_text: str) -> tuple[str | None, str | None]:
    """
    Parse Ollama response to extract title and summary.

    Args:
        response_text: Raw response from Ollama

    Returns:
        Tuple of (title, summary) - either may be None if parsing fails
    """
    title = None
    summary = None

    title_match = TITLE_PATTERN.search(response_text)
    if title_match:
        title = title_match.group(1).strip()
        # Enforce max length
        if len(title) > 100:
            title = title[:97] + "..."

    summary_match = SUMMARY_PATTERN.search(response_text)
    if summary_match:
        summary = summary_match.group(1).strip()

    return title, summary


class Enricher:
    """Ollama-based tweet enricher."""

    def __init__(self, model: str, host: str = "http://localhost:11434"):
        """
        Initialize enricher.

        Args:
            model: Ollama model name (e.g., "qwen3")
            host: Ollama API host URL
        """
        self.model = model
        self.host = host
        self._client = ollama.Client(host=host)

    def check_connection(self) -> tuple[bool, str | None]:
        """
        Verify Ollama is running and model is available.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # List models to verify connection
            models = self._client.list()
            model_names = [m.model for m in models.models]

            # Check if our model is available (handle name variations)
            # Model names can be "qwen3", "qwen3:latest", "qwen3:7b", etc.
            model_base = self.model.split(":")[0]
            available = any(
                m.split(":")[0] == model_base or m == self.model
                for m in model_names
            )

            if not available:
                return False, f"Model '{self.model}' not found. Available: {model_names}"

            return True, None

        except ResponseError as e:
            return False, f"Ollama API error: {e}"
        except Exception as e:
            return False, f"Cannot connect to Ollama at {self.host}: {e}"

    def enrich(self, content: TweetContent) -> EnrichmentResult:
        """
        Generate title and summary for tweet content.

        Args:
            content: TweetContent with author and text

        Returns:
            EnrichmentResult with title and comment
        """
        prompt = PROMPT_TEMPLATE.format(author=content.author, text=content.text)

        try:
            response = self._client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 500,  # Limit response length
                },
            )

            response_text = response.response

            title, summary = parse_response(response_text)

            if not title and not summary:
                return EnrichmentResult(
                    success=False,
                    error_message=f"Failed to parse response: {response_text[:200]}",
                )

            return EnrichmentResult(
                success=True,
                title=title,
                comment=summary,
            )

        except ResponseError as e:
            return EnrichmentResult(
                success=False,
                error_message=f"Ollama API error: {e}",
            )
        except Exception as e:
            return EnrichmentResult(
                success=False,
                error_message=f"Enrichment failed: {e}",
            )

    async def enrich_async(self, content: TweetContent) -> EnrichmentResult:
        """
        Async wrapper for enrich (Ollama client is sync).

        For now, just calls sync method. Can be enhanced with
        asyncio.to_thread if blocking becomes an issue.
        """
        import asyncio

        return await asyncio.to_thread(self.enrich, content)
