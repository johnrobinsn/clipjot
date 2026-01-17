"""Tests for state management."""

import json

import pytest

from state import StateManager


class TestStateManager:
    """Tests for StateManager."""

    def test_load_empty(self, state_file):
        """Loading non-existent file should work."""
        sm = StateManager(state_file, base_delay=35, max_backoff=3600)
        sm.load()  # Should not raise
        assert sm.get_cursor() is None

    def test_save_and_load(self, state_file):
        """Save and load round-trip."""
        sm = StateManager(state_file, base_delay=35, max_backoff=3600)
        sm.set_cursor("12345")
        sm.save()

        # Load in new instance
        sm2 = StateManager(state_file, base_delay=35, max_backoff=3600)
        sm2.load()
        assert sm2.get_cursor() == "12345"

    def test_load_existing_state(self, state_file_with_data):
        """Load from existing state file."""
        sm = StateManager(state_file_with_data, base_delay=35, max_backoff=3600)
        sm.load()

        assert sm.get_cursor() == "12345"
        assert sm.get_retry_count("https://x.com/user/status/111") == 2
        assert sm.is_failed("https://x.com/user/status/222") is True

    def test_cursor_operations(self, state_file):
        """Test cursor get/set/clear."""
        sm = StateManager(state_file, base_delay=35, max_backoff=3600)

        assert sm.get_cursor() is None
        sm.set_cursor("abc123")
        assert sm.get_cursor() == "abc123"
        sm.clear_cursor()
        assert sm.get_cursor() is None

    def test_record_error_increments(self, state_file):
        """Recording errors increments attempt count."""
        sm = StateManager(state_file, base_delay=35, max_backoff=3600)
        url = "https://x.com/user/status/999"

        should_retry = sm.record_error(url, 999, "network", max_attempts=3)
        assert should_retry is True
        assert sm.get_retry_count(url) == 1

        should_retry = sm.record_error(url, 999, "network", max_attempts=3)
        assert should_retry is True
        assert sm.get_retry_count(url) == 2

        should_retry = sm.record_error(url, 999, "network", max_attempts=3)
        assert should_retry is False  # Max reached
        assert sm.is_failed(url) is True

    def test_not_found_fails_immediately(self, state_file):
        """404 errors should fail immediately."""
        sm = StateManager(state_file, base_delay=35, max_backoff=3600)
        url = "https://x.com/user/status/404"

        should_retry = sm.record_error(url, 404, "not_found", max_attempts=3)
        assert should_retry is False
        assert sm.is_failed(url) is True

    def test_record_success_clears_retry(self, state_file):
        """Success should remove from retry queue."""
        sm = StateManager(state_file, base_delay=35, max_backoff=3600)
        url = "https://x.com/user/status/777"

        sm.record_error(url, 777, "network")
        assert sm.get_retry_count(url) == 1

        sm.record_success(url)
        assert sm.get_retry_count(url) == 0

    def test_backoff_operations(self, state_file):
        """Test backoff increment and reset."""
        sm = StateManager(state_file, base_delay=35, max_backoff=3600)

        assert sm.get_current_backoff() == 0

        delay1 = sm.increment_backoff()
        assert delay1 == 35  # base * fib[0]
        assert sm.get_current_backoff() == 35

        delay2 = sm.increment_backoff()
        assert delay2 == 35  # base * fib[1]

        delay3 = sm.increment_backoff()
        assert delay3 == 70  # base * fib[2]

        sm.reset_backoff()
        assert sm.get_current_backoff() == 0

    def test_atomic_write(self, state_file):
        """Save should use atomic write."""
        sm = StateManager(state_file, base_delay=35, max_backoff=3600)
        sm.set_cursor("test")
        sm.save()

        # File should exist and be valid JSON
        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["cursor"] == "test"

    def test_corrupted_state_raises(self, tmp_path):
        """Corrupted state file should raise ValueError."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json")

        sm = StateManager(bad_file, base_delay=35, max_backoff=3600)
        with pytest.raises(ValueError, match="Corrupted"):
            sm.load()
