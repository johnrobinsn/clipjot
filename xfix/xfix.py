#!/usr/bin/env python3
"""XFix - X.com bookmark enricher for ClipJot.

Monitors ClipJot for X.com bookmarks and enriches them with
AI-generated titles and comments using Ollama.
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

from api_client import Bookmark, ClipJotClient, is_placeholder_title
from config import Config, load_config
from enricher import Enricher
from fetcher import ErrorType, RateLimiter, fetch_tweet
from state import StateManager

# Global shutdown flag
shutdown_requested = False


def setup_logging(level: str, verbose: bool) -> logging.Logger:
    """Configure logging with the specified level."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)-5s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("xfix")
    logger.setLevel(log_level)

    # Store verbose flag on logger for access elsewhere
    logger.verbose = verbose  # type: ignore

    return logger


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully. Second signal forces immediate exit."""
    global shutdown_requested
    if shutdown_requested:
        # Second signal - force immediate exit
        logging.getLogger("xfix").info("Forced shutdown")
        sys.exit(1)
    shutdown_requested = True
    logging.getLogger("xfix").info("Shutdown requested, finishing current task...")


async def process_bookmark(
    bookmark: Bookmark,
    client: ClipJotClient,
    enricher: Enricher,
    rate_limiter: RateLimiter,
    state: StateManager,
    logger: logging.Logger,
    dry_run: bool = False,
) -> bool:
    """
    Process a single bookmark: fetch, enrich, update.

    Args:
        bookmark: Bookmark to process
        client: ClipJot API client
        enricher: Ollama enricher
        rate_limiter: X.com rate limiter
        state: State manager
        logger: Logger instance
        dry_run: If True, don't update ClipJot

    Returns:
        True if successful, False otherwise
    """
    url = bookmark.url
    bookmark_id = bookmark.id

    # Check if already permanently failed
    if state.is_failed(url):
        logger.debug(f"Skipping permanently failed URL: {url}")
        return False

    logger.info(f"Processing bookmark {bookmark_id}: {url}")

    # Wait for rate limit
    await rate_limiter.wait()

    # Fetch tweet content
    result = await fetch_tweet(url)

    if not result.success:
        error_type = result.error_type.value if result.error_type else "unknown"
        logger.warning(f"Fetch failed ({error_type}): {result.error_message}")

        # Record error and check if should retry
        should_retry = state.record_error(url, bookmark_id, error_type)

        if result.error_type in (ErrorType.NETWORK, ErrorType.RATE_LIMIT):
            # Increment global backoff
            new_delay = rate_limiter.record_error()
            logger.info(f"Backoff increased to {new_delay:.1f}s")
        elif result.error_type == ErrorType.NOT_FOUND:
            logger.warning(f"Tweet deleted or not found, marking as failed")

        if not should_retry:
            retry_count = state.get_retry_count(url)
            logger.error(f"Max retries ({retry_count}) reached for {url}")

        state.save()
        return False

    # Success - reset backoff
    rate_limiter.record_success()
    content = result.content
    logger.info(f"Fetched tweet content ({len(content.text)} chars)")

    # Determine what needs enrichment
    replacing_title = is_placeholder_title(bookmark.title)
    need_title = not bookmark.title or replacing_title
    need_comment = not bookmark.comment

    # Generate enrichment
    enrich_result = await enricher.enrich_async(content)

    if not enrich_result.success:
        logger.warning(f"Enrichment failed: {enrich_result.error_message}")
        state.record_error(url, bookmark_id, "ollama")
        state.save()
        return False

    # Prepare update
    new_title = enrich_result.title if need_title else None
    new_comment = content.to_markdown() if need_comment else None

    # Log the generated content
    if logger.verbose:  # type: ignore
        logger.info(f"Enriched bookmark {bookmark_id}")
        logger.info(f"  URL: {url}")
        if new_title:
            if replacing_title:
                logger.info(f"  Title: {new_title} (replacing: {bookmark.title!r})")
            else:
                logger.info(f"  Title: {new_title}")
        if new_comment:
            # Indent multi-line comments
            comment_lines = new_comment.split("\n")
            logger.info(f"  Comment: {comment_lines[0]}")
            for line in comment_lines[1:]:
                logger.info(f"           {line}")
    else:
        logger.info(f"Enriched: {url}")

    # Update ClipJot
    if not dry_run:
        try:
            await client.edit_bookmark(
                bookmark_id=bookmark_id,
                title=new_title,
                comment=new_comment,
            )
            logger.info(f"Updated bookmark {bookmark_id} successfully")
        except Exception as e:
            logger.error(f"Failed to update bookmark: {e}")
            state.record_error(url, bookmark_id, "network")
            state.save()
            return False
    else:
        logger.info(f"[DRY RUN] Would update bookmark {bookmark_id}")

    # Record success
    state.record_success(url)
    state.save()
    return True


async def main_loop(
    config: Config,
    client: ClipJotClient,
    enricher: Enricher,
    state: StateManager,
    logger: logging.Logger,
    dry_run: bool = False,
) -> None:
    """Main processing loop with long-polling."""
    global shutdown_requested

    rate_limiter = RateLimiter(
        min_delay=config.fetch_min_delay,
        max_delay=config.fetch_max_delay,
        max_backoff=config.fetch_max_backoff,
    )

    cursor = state.get_cursor()
    if cursor:
        logger.info(f"Resuming from cursor: {cursor}")
    else:
        logger.info("Starting from beginning (no saved cursor)")

    while not shutdown_requested:
        try:
            # Sync with ClipJot (long-polling)
            logger.debug(f"Syncing from cursor: {cursor}")
            bookmarks, new_cursor, has_more = await client.get_x_bookmarks_needing_enrichment(
                cursor=cursor,
                limit=50,
                wait=True,
            )

            # Update cursor immediately
            if new_cursor and new_cursor != cursor:
                cursor = new_cursor
                state.set_cursor(cursor)

            if not bookmarks:
                logger.debug("No new X.com bookmarks needing enrichment")
                continue

            logger.info(f"Found {len(bookmarks)} X.com bookmarks to process")

            # Process each bookmark
            for bookmark in bookmarks:
                if shutdown_requested:
                    logger.info("Shutdown requested, stopping after current bookmark")
                    break

                await process_bookmark(
                    bookmark=bookmark,
                    client=client,
                    enricher=enricher,
                    rate_limiter=rate_limiter,
                    state=state,
                    logger=logger,
                    dry_run=dry_run,
                )

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            # Wait a bit before retrying
            await asyncio.sleep(10)

    logger.info("Shutdown complete")


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="XFix - X.com bookmark enricher for ClipJot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--from-start",
        action="store_true",
        help="Ignore saved cursor, process all bookmarks from beginning",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and generate content but don't update ClipJot API",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show full generated content in logs",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Minimal output (only errors and summaries)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Path to .env file (default: .env in current directory)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.env_file)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    # Determine verbosity
    verbose = config.log_verbose
    if args.verbose:
        verbose = True
    if args.quiet:
        verbose = False

    # Setup logging
    logger = setup_logging(config.log_level, verbose)

    logger.info("XFix starting...")
    logger.info(f"ClipJot API: {config.clipjot_api_url}")
    logger.info(f"Ollama model: {config.ollama_model}")

    if args.dry_run:
        logger.info("DRY RUN MODE - no changes will be made")

    # Initialize components
    client = ClipJotClient(config.clipjot_api_url, config.clipjot_api_token)
    enricher = Enricher(config.ollama_model, config.ollama_host)

    # Check Ollama connection
    logger.info("Checking Ollama connection...")
    ok, error = enricher.check_connection()
    if not ok:
        logger.error(f"Ollama check failed: {error}")
        return 1
    logger.info("Ollama connection OK")

    # Initialize state
    base_delay = (config.fetch_min_delay + config.fetch_max_delay) / 2
    state = StateManager(
        config.state_file,
        base_delay=base_delay,
        max_backoff=config.fetch_max_backoff,
    )

    try:
        state.load()
        logger.debug(f"Loaded state from {config.state_file}")
    except ValueError as e:
        logger.warning(f"Could not load state: {e}")
        logger.info("Starting with fresh state")
    except FileNotFoundError:
        logger.debug("No existing state file, starting fresh")

    # Handle --from-start
    if args.from_start:
        logger.info("--from-start: clearing saved cursor")
        state.clear_cursor()

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run main loop
    try:
        asyncio.run(
            main_loop(
                config=config,
                client=client,
                enricher=enricher,
                state=state,
                logger=logger,
                dry_run=args.dry_run,
            )
        )
    except KeyboardInterrupt:
        logger.info("Interrupted")

    # Final state save
    state.save()
    logger.info("State saved")

    return 0


if __name__ == "__main__":
    sys.exit(main())
