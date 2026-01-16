#!/usr/bin/env python3
"""Example client script for watching new bookmarks via long polling.

Usage:
    1. Copy .env.example to .env in this directory
    2. Set LINKJOT_API_TOKEN in .env
    3. Run: python sync_watch.py

The script will:
    1. Skip to the latest bookmark (ignoring existing ones)
    2. Long poll for new bookmarks
    3. Print each new bookmark as it arrives
"""

import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Set env vars manually.")
    print("Install with: pip install python-dotenv")

import requests

API_TOKEN = os.getenv("LINKJOT_API_TOKEN")
BASE_URL = os.getenv("LINKJOT_BASE_URL", "http://localhost:5001")

if not API_TOKEN:
    print("Error: LINKJOT_API_TOKEN not set in environment")
    print("Create a .env file with: LINKJOT_API_TOKEN=your-token-here")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}


def sync(cursor=None, skip_to_latest=False, wait=False):
    """Call the sync API."""
    response = requests.post(
        f"{BASE_URL}/api/v1/bookmarks/sync",
        headers=HEADERS,
        json={
            "cursor": cursor,
            "skip_to_latest": skip_to_latest,
            "wait": wait,
        },
        timeout=60,  # Longer timeout for long polling
    )
    if not response.ok:
        print(f"Error: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except Exception:
            print(f"Response: {response.text[:200]}")
        sys.exit(1)
    return response.json()


def main():
    print(f"Connecting to {BASE_URL}...")

    # Skip to latest - ignore existing bookmarks
    print("Skipping to latest bookmark...")
    result = sync(skip_to_latest=True)
    cursor = result["cursor"]
    print(f"Starting cursor: {cursor}")
    print("Watching for new bookmarks (Ctrl+C to stop)...\n")

    try:
        while True:
            # Long poll for new bookmarks
            result = sync(cursor=cursor, wait=True)

            if result["bookmarks"]:
                for bm in result["bookmarks"]:
                    print(f"New bookmark: {bm['title'] or bm['url']}")
                    print(f"  URL: {bm['url']}")
                    if bm["tags"]:
                        tags = ", ".join(t["name"] for t in bm["tags"])
                        print(f"  Tags: {tags}")
                    print()
                cursor = result["cursor"]
            else:
                # Timeout with no new bookmarks, continue polling
                pass

    except KeyboardInterrupt:
        print("\nStopped watching.")


if __name__ == "__main__":
    main()
