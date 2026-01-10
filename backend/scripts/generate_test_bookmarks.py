#!/usr/bin/env python3
"""Generate fake bookmarks for testing the UI with large datasets.

Usage:
    python -m scripts.generate_test_bookmarks --user-id 1 --count 100
    python -m scripts.generate_test_bookmarks --email user@example.com --count 500
"""

import argparse
import random
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import db as database
from app.models import Bookmark, Tag

# Sample data for generating fake bookmarks
DOMAINS = [
    "github.com", "stackoverflow.com", "medium.com", "dev.to", "hackernews.com",
    "reddit.com", "twitter.com", "youtube.com", "wikipedia.org", "python.org",
    "rust-lang.org", "golang.org", "nodejs.org", "reactjs.org", "vuejs.org",
    "angular.io", "svelte.dev", "tailwindcss.com", "daisyui.com", "htmx.org",
    "fastapi.tiangolo.com", "flask.palletsprojects.com", "djangoproject.com",
    "aws.amazon.com", "cloud.google.com", "azure.microsoft.com", "vercel.com",
    "netlify.com", "heroku.com", "digitalocean.com", "docker.com", "kubernetes.io",
]

TITLE_PREFIXES = [
    "How to", "Getting Started with", "Introduction to", "Advanced", "Understanding",
    "Building", "Creating", "Deploying", "Testing", "Debugging", "Optimizing",
    "Best Practices for", "A Guide to", "Tutorial:", "Deep Dive into", "Mastering",
]

TITLE_SUBJECTS = [
    "Python", "JavaScript", "TypeScript", "Rust", "Go", "React", "Vue", "Angular",
    "Node.js", "FastAPI", "Django", "Flask", "Docker", "Kubernetes", "AWS", "GCP",
    "Machine Learning", "Data Science", "Web Development", "API Design", "Testing",
    "CI/CD", "DevOps", "Microservices", "GraphQL", "REST APIs", "WebSockets",
    "Authentication", "Security", "Performance", "Caching", "Databases", "SQL",
]

COMMENTS = [
    "Very helpful article, saved for later reference.",
    "Great tutorial, worked perfectly!",
    "Need to try this approach in my project.",
    "Interesting perspective on the topic.",
    "Bookmarked for the team to review.",
    "Good examples and explanations.",
    "Might be useful for the upcoming sprint.",
    "Reference material for documentation.",
    "Check back later for updates.",
    "Recommended by a colleague.",
    None, None, None, None, None,  # More likely to have no comment
]

TAG_NAMES = [
    "python", "javascript", "tutorial", "reference", "devops", "frontend",
    "backend", "database", "security", "testing", "tools", "learning",
    "career", "productivity", "design", "api", "cloud", "opensource",
]


def generate_url(domain: str) -> str:
    """Generate a fake URL."""
    path_parts = random.randint(1, 3)
    path = "/".join(
        random.choice(["blog", "docs", "guide", "article", "post", "tutorial", "ref"])
        + "-" + str(random.randint(1000, 9999))
        for _ in range(path_parts)
    )
    return f"https://{domain}/{path}"


def generate_title() -> str:
    """Generate a fake title."""
    prefix = random.choice(TITLE_PREFIXES)
    subject = random.choice(TITLE_SUBJECTS)
    suffix = random.choice(["", " in 2024", " - Complete Guide", " for Beginners", " Tutorial"])
    return f"{prefix} {subject}{suffix}"


def get_or_create_tags(db, user_id: int, tag_names: list[str]) -> list[int]:
    """Get or create tags by name, return list of tag IDs."""
    tag_ids = []
    for name in tag_names:
        tag = database.get_tag_by_name(db, user_id, name)
        if not tag:
            tag = database.create_tag(db, user_id, name)
        tag_ids.append(tag.id)
    return tag_ids


def generate_bookmarks(db, user_id: int, count: int):
    """Generate fake bookmarks for a user."""
    print(f"Generating {count} bookmarks for user {user_id}...")

    # Ensure some tags exist
    all_tag_ids = get_or_create_tags(db, user_id, TAG_NAMES)

    for i in range(count):
        domain = random.choice(DOMAINS)
        url = generate_url(domain)
        title = generate_title()
        comment = random.choice(COMMENTS)

        # Create bookmark
        bookmark = Bookmark(
            user_id=user_id,
            url=url,
            title=title,
            comment=comment,
            client_name="test-generator",
        )
        bookmark = database.create_bookmark(db, bookmark)

        # Assign random tags (0-4 tags per bookmark)
        num_tags = random.randint(0, 4)
        if num_tags > 0:
            selected_tag_ids = random.sample(all_tag_ids, min(num_tags, len(all_tag_ids)))
            database.set_bookmark_tags(db, bookmark.id, selected_tag_ids)

        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} bookmarks...")

    print(f"Done! Created {count} bookmarks.")


def main():
    parser = argparse.ArgumentParser(description="Generate fake bookmarks for testing")
    parser.add_argument("--user-id", type=int, help="User ID to create bookmarks for")
    parser.add_argument("--email", type=str, help="User email to create bookmarks for")
    parser.add_argument("--count", type=int, default=100, help="Number of bookmarks to create (default: 100)")

    args = parser.parse_args()

    if not args.user_id and not args.email:
        parser.error("Either --user-id or --email is required")

    db = database.get_db()

    # Find user
    if args.user_id:
        user = database.get_user_by_id(db, args.user_id)
        if not user:
            print(f"Error: User with ID {args.user_id} not found")
            sys.exit(1)
    else:
        user = database.get_user_by_email(db, args.email)
        if not user:
            print(f"Error: User with email {args.email} not found")
            sys.exit(1)

    print(f"Found user: {user.email} (ID: {user.id})")
    generate_bookmarks(db, user.id, args.count)


if __name__ == "__main__":
    main()
