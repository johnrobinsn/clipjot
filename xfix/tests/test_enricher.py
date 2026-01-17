"""Tests for Ollama enricher."""

import pytest

from enricher import parse_response


class TestParseResponse:
    """Tests for Ollama response parsing."""

    def test_standard_format(self, sample_ollama_response):
        title, summary = parse_response(sample_ollama_response)
        assert title == "AI and ML developments discussed by testuser"
        assert "artificial intelligence" in summary

    def test_title_truncation(self):
        long_title = "A" * 150
        response = f"TITLE: {long_title}\nSUMMARY: Short summary"
        title, summary = parse_response(response)
        assert len(title) == 100
        assert title.endswith("...")

    def test_multiline_summary(self):
        response = """TITLE: Test title
SUMMARY: First sentence.
Second sentence.
Third sentence."""
        title, summary = parse_response(response)
        assert title == "Test title"
        assert "First sentence" in summary
        assert "Third sentence" in summary

    def test_case_insensitive(self):
        response = "title: My Title\nsummary: My Summary"
        title, summary = parse_response(response)
        assert title == "My Title"
        assert summary == "My Summary"

    def test_extra_whitespace(self):
        response = "TITLE:   Spaced Title   \nSUMMARY:   Spaced Summary   "
        title, summary = parse_response(response)
        assert title == "Spaced Title"
        assert summary == "Spaced Summary"

    def test_missing_title(self):
        response = "SUMMARY: Only summary provided"
        title, summary = parse_response(response)
        assert title is None
        assert summary == "Only summary provided"

    def test_missing_summary(self):
        response = "TITLE: Only title provided"
        title, summary = parse_response(response)
        assert title == "Only title provided"
        assert summary is None

    def test_empty_response(self):
        title, summary = parse_response("")
        assert title is None
        assert summary is None

    def test_malformed_response(self):
        response = "This response doesn't follow the expected format at all."
        title, summary = parse_response(response)
        assert title is None
        assert summary is None
