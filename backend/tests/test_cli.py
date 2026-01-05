"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from app.cli import cli
from app import db as database


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_db(db, test_user):
    """Mock the database getter to use test database."""
    with patch("app.cli.database.get_db", return_value=db):
        yield db


class TestDatabaseCommands:
    """Test database CLI commands."""

    def test_db_init(self, runner, mock_db):
        """Test database initialization command."""
        result = runner.invoke(cli, ["db", "init"])

        assert result.exit_code == 0
        assert "initialized" in result.output.lower()

    def test_db_migrate(self, runner, mock_db):
        """Test database migration command."""
        result = runner.invoke(cli, ["db", "migrate"])

        assert result.exit_code == 0


class TestUserCommands:
    """Test user CLI commands."""

    def test_user_list(self, runner, mock_db, test_user):
        """Test listing users."""
        result = runner.invoke(cli, ["user", "list"])

        assert result.exit_code == 0
        assert test_user.email in result.output

    def test_user_list_json(self, runner, mock_db, test_user):
        """Test listing users as JSON."""
        result = runner.invoke(cli, ["user", "list", "--format", "json"])

        assert result.exit_code == 0
        assert test_user.email in result.output
        assert '"email"' in result.output

    def test_user_info(self, runner, mock_db, test_user):
        """Test showing user info."""
        result = runner.invoke(cli, ["user", "info", test_user.email])

        assert result.exit_code == 0
        assert test_user.email in result.output

    def test_user_info_not_found(self, runner, mock_db):
        """Test showing info for nonexistent user."""
        result = runner.invoke(cli, ["user", "info", "nonexistent@example.com"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_user_suspend(self, runner, mock_db, test_user):
        """Test suspending a user."""
        result = runner.invoke(cli, [
            "user", "suspend", test_user.email,
            "--reason", "Test suspension"
        ])

        assert result.exit_code == 0
        assert "suspended" in result.output.lower()

        # Verify suspension
        db = mock_db
        user = database.get_user_by_email(db, test_user.email)
        assert user.is_suspended is True
        assert user.suspended_reason == "Test suspension"

    def test_user_unsuspend(self, runner, mock_db, test_user):
        """Test unsuspending a user."""
        # First suspend
        test_user.is_suspended = True
        database.update_user(mock_db, test_user)

        result = runner.invoke(cli, ["user", "unsuspend", test_user.email])

        assert result.exit_code == 0
        assert "unsuspended" in result.output.lower()


class TestAdminCommands:
    """Test admin CLI commands."""

    def test_admin_init(self, runner, mock_db, test_user):
        """Test bootstrapping first admin."""
        result = runner.invoke(cli, ["admin", "init", test_user.email])

        assert result.exit_code == 0
        assert "admin" in result.output.lower()

        # Verify admin status
        user = database.get_user_by_email(mock_db, test_user.email)
        assert user.is_admin is True

    def test_admin_init_when_admins_exist(self, runner, mock_db, admin_user):
        """Test that admin init fails when admins exist."""
        result = runner.invoke(cli, ["admin", "init", admin_user.email])

        assert result.exit_code != 0
        assert "already exist" in result.output.lower()

    def test_admin_grant(self, runner, mock_db, test_user):
        """Test granting admin privileges."""
        result = runner.invoke(cli, ["admin", "grant", test_user.email])

        assert result.exit_code == 0

        user = database.get_user_by_email(mock_db, test_user.email)
        assert user.is_admin is True

    def test_admin_revoke(self, runner, mock_db, test_user, admin_user):
        """Test revoking admin privileges."""
        # Make test_user an admin first
        test_user.is_admin = True
        database.update_user(mock_db, test_user)

        result = runner.invoke(cli, ["admin", "revoke", test_user.email])

        assert result.exit_code == 0

        user = database.get_user_by_email(mock_db, test_user.email)
        assert user.is_admin is False

    def test_admin_revoke_last_admin(self, runner, mock_db, admin_user):
        """Test that revoking the last admin fails."""
        result = runner.invoke(cli, ["admin", "revoke", admin_user.email])

        assert result.exit_code != 0
        assert "last admin" in result.output.lower()

    def test_admin_list(self, runner, mock_db, admin_user):
        """Test listing admin users."""
        result = runner.invoke(cli, ["admin", "list"])

        assert result.exit_code == 0
        assert admin_user.email in result.output


class TestCleanupCommands:
    """Test cleanup CLI commands."""

    def test_cleanup_sessions_dry_run(self, runner, mock_db):
        """Test session cleanup with dry run."""
        result = runner.invoke(cli, ["cleanup", "sessions", "--dry-run"])

        assert result.exit_code == 0
        assert "would delete" in result.output.lower()

    def test_cleanup_tokens_dry_run(self, runner, mock_db):
        """Test token cleanup with dry run."""
        result = runner.invoke(cli, ["cleanup", "tokens", "--dry-run"])

        assert result.exit_code == 0
        assert "would delete" in result.output.lower()


class TestStatsCommand:
    """Test stats command."""

    def test_stats(self, runner, mock_db, test_user, test_bookmark):
        """Test displaying statistics."""
        with patch("app.cli.config.DATABASE_PATH", ":memory:"):
            result = runner.invoke(cli, ["stats"])

        assert result.exit_code == 0
        assert "Users" in result.output
        assert "Bookmarks" in result.output


class TestTokenCommands:
    """Test token CLI commands."""

    def test_token_create(self, runner, mock_db, test_user):
        """Test creating an API token."""
        result = runner.invoke(cli, [
            "token", "create", test_user.email,
            "--name", "CLI Token",
            "--scope", "write",
        ])

        assert result.exit_code == 0
        assert "TOKEN" in result.output

    def test_token_list(self, runner, mock_db, test_user, test_token):
        """Test listing API tokens."""
        result = runner.invoke(cli, ["token", "list", test_user.email])

        assert result.exit_code == 0
        assert "Test Token" in result.output

    def test_token_revoke(self, runner, mock_db, test_user, test_token):
        """Test revoking an API token."""
        result = runner.invoke(cli, [
            "token", "revoke", test_user.email,
            "--name", "Test Token",
        ])

        assert result.exit_code == 0
        assert "revoked" in result.output.lower()
