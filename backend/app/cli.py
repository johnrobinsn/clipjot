"""LinkJot CLI - Administrative command-line interface.

Usage: linkjot <command> [options]

Commands for database management, user administration, and maintenance.
"""

import os
import sys
import json
import click
from datetime import datetime

from . import config
from . import db as database
from . import auth
from .models import now_iso, future_iso


# =============================================================================
# CLI Group
# =============================================================================

@click.group()
@click.version_option(version="0.1.0", prog_name="linkjot")
def cli():
    """LinkJot administration CLI."""
    pass


# =============================================================================
# Database Commands
# =============================================================================

@cli.group()
def db():
    """Database management commands."""
    pass


@db.command("init")
def db_init():
    """Initialize database schema.

    Creates all tables, indexes, and triggers. Safe to run multiple times.
    """
    click.echo(f"Initializing database at {config.DATABASE_PATH}...")
    db = database.get_db()
    database.init_db(db)
    click.echo("Database initialized successfully.")


@db.command("migrate")
def db_migrate():
    """Run pending database migrations.

    Note: Currently a no-op as migrations are handled by FastLite's transform.
    """
    click.echo("Checking for pending migrations...")
    # FastLite handles schema changes via transform=True
    click.echo("No pending migrations.")


@db.command("backup")
@click.argument("path")
def db_backup(path):
    """Create a backup of the database.

    PATH: Destination file path for the backup.
    """
    import sqlite3

    if not os.path.exists(config.DATABASE_PATH):
        click.echo(f"Error: Database not found at {config.DATABASE_PATH}", err=True)
        sys.exit(4)

    click.echo(f"Backing up database to {path}...")

    # Use SQLite's backup API
    source = sqlite3.connect(config.DATABASE_PATH)
    dest = sqlite3.connect(path)

    with dest:
        source.backup(dest)

    source.close()
    dest.close()

    click.echo(f"Backup completed: {path}")


# =============================================================================
# User Commands
# =============================================================================

@cli.group()
def user():
    """User management commands."""
    pass


@user.command("list")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "csv"]), default="table",
              help="Output format")
def user_list(output_format):
    """List all users with summary statistics."""
    db = database.get_db()
    users = database.get_all_users(db, limit=1000)

    if output_format == "json":
        data = []
        for u in users:
            stats = database.get_user_stats(db, u.id)
            data.append({
                "id": u.id,
                "email": u.email,
                "created_at": u.created_at,
                "bookmarks": stats["bookmark_count"],
                "tags": stats["tag_count"],
                "is_premium": u.is_premium,
                "is_admin": u.is_admin,
                "is_suspended": u.is_suspended,
            })
        click.echo(json.dumps(data, indent=2))

    elif output_format == "csv":
        click.echo("id,email,created_at,bookmarks,tags,premium,admin,suspended")
        for u in users:
            stats = database.get_user_stats(db, u.id)
            click.echo(f"{u.id},{u.email},{u.created_at},{stats['bookmark_count']},{stats['tag_count']},{u.is_premium},{u.is_admin},{u.is_suspended}")

    else:  # table
        click.echo(f"{'ID':<6} {'Email':<40} {'Bookmarks':<10} {'Tags':<6} {'Status':<20}")
        click.echo("-" * 90)
        for u in users:
            stats = database.get_user_stats(db, u.id)
            status = []
            if u.is_admin:
                status.append("admin")
            if u.is_premium:
                status.append("premium")
            if u.is_suspended:
                status.append("suspended")
            status_str = ", ".join(status) or "active"
            click.echo(f"{u.id:<6} {u.email:<40} {stats['bookmark_count']:<10} {stats['tag_count']:<6} {status_str:<20}")

    click.echo(f"\nTotal: {len(users)} users")


@user.command("info")
@click.argument("email")
def user_info(email):
    """Show detailed information for a user.

    EMAIL: User's email address.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    stats = database.get_user_stats(db, user.id)

    click.echo(f"User: {user.email}")
    click.echo(f"  ID: {user.id}")
    click.echo(f"  Created: {user.created_at}")
    click.echo(f"  Premium: {user.is_premium}")
    click.echo(f"  Admin: {user.is_admin}")
    click.echo(f"  Suspended: {user.is_suspended}")
    if user.is_suspended:
        click.echo(f"    Reason: {user.suspended_reason}")
        click.echo(f"    Since: {user.suspended_at}")
    click.echo(f"  Bookmarks: {stats['bookmark_count']}")
    click.echo(f"  Tags: {stats['tag_count']}")
    click.echo(f"  Active Sessions: {stats['session_count']}")
    click.echo(f"  API Tokens: {stats['token_count']}")


@user.command("export")
@click.argument("email")
@click.option("--output", "-o", type=click.Path(), help="Output file path (default: stdout)")
def user_export(email, output):
    """Export a user's bookmarks as JSON.

    EMAIL: User's email address.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    # Get all bookmarks
    bookmarks = []
    offset = 0
    while True:
        batch = database.get_user_bookmarks(db, user.id, 500, offset)
        if not batch:
            break
        for b in batch:
            tags = database.get_bookmark_tags(db, b.id)
            bookmarks.append({
                "url": b.url,
                "title": b.title,
                "comment": b.comment,
                "tags": [t.name for t in tags],
                "created_at": b.created_at,
            })
        offset += 500
        if len(batch) < 500:
            break

    export_data = {
        "user": email,
        "bookmarks": bookmarks,
        "exported_at": now_iso(),
        "count": len(bookmarks),
    }

    json_str = json.dumps(export_data, indent=2)

    if output:
        with open(output, "w") as f:
            f.write(json_str)
        click.echo(f"Exported {len(bookmarks)} bookmarks to {output}")
    else:
        click.echo(json_str)


@user.command("delete")
@click.argument("email")
@click.option("--force", is_flag=True, help="Skip confirmation")
def user_delete(email, force):
    """Delete a user and all their data.

    EMAIL: User's email address.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    stats = database.get_user_stats(db, user.id)

    if not force:
        click.echo(f"About to delete user: {user.email}")
        click.echo(f"  Bookmarks: {stats['bookmark_count']}")
        click.echo(f"  Tags: {stats['tag_count']}")
        if not click.confirm("Are you sure you want to delete this user and ALL their data?"):
            click.echo("Cancelled.")
            return

    database.delete_user(db, user.id)
    click.echo(f"User {email} and all their data have been deleted.")


@user.command("suspend")
@click.argument("email")
@click.option("--reason", "-r", required=True, help="Reason for suspension")
def user_suspend(email, reason):
    """Suspend a user account.

    EMAIL: User's email address.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    if user.is_suspended:
        click.echo(f"User {email} is already suspended.")
        return

    user.is_suspended = True
    user.suspended_at = now_iso()
    user.suspended_reason = reason
    database.update_user(db, user)

    # Terminate all sessions
    database.delete_user_sessions(db, user.id)

    click.echo(f"User {email} has been suspended.")
    click.echo(f"Reason: {reason}")
    click.echo(f"All active sessions have been terminated.")


@user.command("unsuspend")
@click.argument("email")
def user_unsuspend(email):
    """Unsuspend a user account.

    EMAIL: User's email address.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    if not user.is_suspended:
        click.echo(f"User {email} is not suspended.")
        return

    user.is_suspended = False
    user.suspended_at = None
    user.suspended_reason = None
    database.update_user(db, user)

    click.echo(f"User {email} has been unsuspended.")


# =============================================================================
# Admin Commands
# =============================================================================

@cli.group("admin")
def admin_group():
    """Admin management commands."""
    pass


@admin_group.command("init")
@click.argument("email")
def admin_init(email):
    """Bootstrap the first admin user.

    Only works when no admin users exist.
    EMAIL: Email of user to make admin.
    """
    db = database.get_db()

    # Check if any admins exist
    admins = list(db.t.user(where="is_admin = 1", limit=1))
    if admins:
        click.echo("Error: Admin users already exist. Use 'linkjot admin grant' instead.", err=True)
        sys.exit(5)

    user = database.get_user_by_email(db, email)
    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    user.is_admin = True
    database.update_user(db, user)

    click.echo(f"User {email} is now an admin.")


@admin_group.command("grant")
@click.argument("email")
def admin_grant(email):
    """Grant admin privileges to a user.

    EMAIL: Email of user to make admin.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    if user.is_admin:
        click.echo(f"User {email} is already an admin.")
        return

    user.is_admin = True
    database.update_user(db, user)

    click.echo(f"User {email} is now an admin.")


@admin_group.command("revoke")
@click.argument("email")
def admin_revoke(email):
    """Revoke admin privileges from a user.

    EMAIL: Email of user to remove from admin.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    if not user.is_admin:
        click.echo(f"User {email} is not an admin.")
        return

    # Check if this is the last admin
    admin_count = db.execute("SELECT COUNT(*) FROM user WHERE is_admin = 1").fetchone()[0]
    if admin_count <= 1:
        click.echo("Error: Cannot revoke the last admin.", err=True)
        sys.exit(5)

    user.is_admin = False
    database.update_user(db, user)

    click.echo(f"Admin privileges revoked from {email}.")


@admin_group.command("list")
def admin_list():
    """List all admin users."""
    db = database.get_db()
    admins = list(db.t.user(where="is_admin = 1"))

    if not admins:
        click.echo("No admin users.")
        return

    click.echo("Admin users:")
    for admin in admins:
        # FastLite returns dicts, so use dict access
        email = admin['email'] if isinstance(admin, dict) else admin.email
        click.echo(f"  - {email}")


# =============================================================================
# Maintenance Commands
# =============================================================================

@cli.group()
def cleanup():
    """Maintenance and cleanup commands."""
    pass


@cleanup.command("sessions")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting")
def cleanup_sessions(dry_run):
    """Remove expired sessions."""
    db = database.get_db()
    now = now_iso()

    count = db.execute(f"SELECT COUNT(*) FROM session WHERE expires_at <= '{now}'").fetchone()[0]

    if dry_run:
        click.echo(f"Would delete {count} expired sessions.")
    else:
        database.cleanup_expired_sessions(db)
        click.echo(f"Deleted {count} expired sessions.")


@cleanup.command("tokens")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting")
def cleanup_tokens(dry_run):
    """Remove expired API tokens."""
    db = database.get_db()
    now = now_iso()

    count = db.execute(f"SELECT COUNT(*) FROM api_token WHERE expires_at <= '{now}'").fetchone()[0]

    if dry_run:
        click.echo(f"Would delete {count} expired tokens.")
    else:
        database.cleanup_expired_tokens(db)
        click.echo(f"Deleted {count} expired tokens.")


@cli.command()
def stats():
    """Display database statistics."""
    db = database.get_db()

    total_users = database.count_all_users(db)
    premium_users = db.execute("SELECT COUNT(*) FROM user WHERE is_premium = 1").fetchone()[0]
    admin_users = db.execute("SELECT COUNT(*) FROM user WHERE is_admin = 1").fetchone()[0]
    suspended_users = db.execute("SELECT COUNT(*) FROM user WHERE is_suspended = 1").fetchone()[0]

    total_bookmarks = database.count_all_bookmarks(db)
    total_tags = db.execute("SELECT COUNT(*) FROM tag").fetchone()[0]
    active_sessions = database.count_active_sessions(db)
    total_tokens = db.execute("SELECT COUNT(*) FROM api_token").fetchone()[0]

    # Database size
    try:
        db_size = os.path.getsize(config.DATABASE_PATH)
        db_size_str = f"{db_size / 1024 / 1024:.2f} MB"
    except Exception:
        db_size_str = "Unknown"

    click.echo("LinkJot Statistics")
    click.echo("=" * 40)
    click.echo(f"Users:")
    click.echo(f"  Total: {total_users}")
    click.echo(f"  Premium: {premium_users}")
    click.echo(f"  Admin: {admin_users}")
    click.echo(f"  Suspended: {suspended_users}")
    click.echo()
    click.echo(f"Content:")
    click.echo(f"  Bookmarks: {total_bookmarks}")
    click.echo(f"  Tags: {total_tags}")
    click.echo()
    click.echo(f"Sessions:")
    click.echo(f"  Active: {active_sessions}")
    click.echo(f"  API Tokens: {total_tokens}")
    click.echo()
    click.echo(f"Database:")
    click.echo(f"  Path: {config.DATABASE_PATH}")
    click.echo(f"  Size: {db_size_str}")


# =============================================================================
# Token Commands
# =============================================================================

@cli.group()
def token():
    """API token management commands."""
    pass


@token.command("create")
@click.argument("email")
@click.option("--name", "-n", required=True, help="Token name")
@click.option("--scope", "-s", type=click.Choice(["read", "write"]), required=True, help="Token scope")
@click.option("--expires", "-e", type=int, default=365, help="Days until expiration (default: 365)")
def token_create(email, name, scope, expires):
    """Create an API token for a user.

    EMAIL: User's email address.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    plaintext, token_obj = auth.create_api_token(db, user.id, name, scope, expires)

    click.echo(f"Token created for {email}")
    click.echo(f"  Name: {name}")
    click.echo(f"  Scope: {scope}")
    click.echo(f"  Expires: {token_obj.expires_at[:10]}")
    click.echo()
    click.echo("TOKEN (save this, it won't be shown again):")
    click.echo(plaintext)


@token.command("list")
@click.argument("email")
def token_list(email):
    """List API tokens for a user.

    EMAIL: User's email address.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    tokens = database.get_user_tokens(db, user.id)

    if not tokens:
        click.echo(f"No API tokens for {email}")
        return

    click.echo(f"API tokens for {email}:")
    click.echo(f"{'Name':<30} {'Scope':<10} {'Expires':<12} {'Last Used':<12}")
    click.echo("-" * 70)
    for t in tokens:
        last_used = t.last_used_at[:10] if t.last_used_at else "Never"
        click.echo(f"{t.name:<30} {t.scope:<10} {t.expires_at[:10]:<12} {last_used:<12}")


@token.command("revoke")
@click.argument("email")
@click.option("--name", "-n", required=True, help="Token name to revoke")
def token_revoke(email, name):
    """Revoke an API token.

    EMAIL: User's email address.
    """
    db = database.get_db()
    user = database.get_user_by_email(db, email)

    if not user:
        click.echo(f"Error: User not found: {email}", err=True)
        sys.exit(3)

    tokens = database.get_user_tokens(db, user.id)
    token = next((t for t in tokens if t.name == name), None)

    if not token:
        click.echo(f"Error: Token '{name}' not found for {email}", err=True)
        sys.exit(3)

    database.delete_token(db, token.id)
    click.echo(f"Token '{name}' has been revoked.")


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
