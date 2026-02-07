"""Reusable FastHTML/FT components for ClipJot UI.

These components provide consistent styling using DaisyUI classes.
"""

import json

from fasthtml.common import *
from typing import Optional
from urllib.parse import urlparse

from . import config
from .models import Bookmark, Tag, User


# =============================================================================
# Heroicons SVG Helper
# =============================================================================

def heroicon(name: str, size: str = "w-5 h-5", cls: str = "", **attrs):
    """Generate Heroicons SVG elements.

    Args:
        name: Icon name (e.g., 'bookmark', 'x-mark', 'pencil-square')
        size: Tailwind size classes (default: 'w-5 h-5')
        cls: Additional CSS classes
        **attrs: Additional SVG attributes

    Returns:
        SVG element for the specified icon
    """
    icons = {
        # Bookmark icon (solid) - brand icon
        "bookmark": '''<path fill-rule="evenodd" d="M6.32 2.577a49.255 49.255 0 0 1 11.36 0c1.497.174 2.57 1.46 2.57 2.93V21a.75.75 0 0 1-1.085.67L12 18.089l-7.165 3.583A.75.75 0 0 1 3.75 21V5.507c0-1.47 1.073-2.756 2.57-2.93Z" clip-rule="evenodd" />''',

        # X mark (outline) - close buttons
        "x-mark": '''<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />''',

        # Pencil square (outline) - edit/note indicator
        "pencil-square": '''<path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />''',

        # Pencil (outline) - simple edit icon
        "pencil": '''<path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />''',

        # Tag (outline) - for tags/organization
        "tag": '''<path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 0 0 3 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 0 0 5.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 0 0 9.568 3Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6Z" />''',

        # Globe (outline) - for sync/everywhere
        "globe-alt": '''<path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418" />''',

        # Share (outline) - for sharing
        "share": '''<path stroke-linecap="round" stroke-linejoin="round" d="M7.217 10.907a2.25 2.25 0 1 0 0 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186 9.566-5.314m-9.566 7.5 9.566 5.314m0 0a2.25 2.25 0 1 0 3.935 2.186 2.25 2.25 0 0 0-3.935-2.186Zm0-12.814a2.25 2.25 0 1 0 3.933-2.185 2.25 2.25 0 0 0-3.933 2.185Z" />''',

        # Code bracket (outline) - for API/developer
        "code-bracket": '''<path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />''',

        # Rocket launch (outline) - for building/launching
        "rocket-launch": '''<path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 0 1-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 0 0 6.16-12.12A14.98 14.98 0 0 0 9.631 8.41m5.96 5.96a14.926 14.926 0 0 1-5.841 2.58m-.119-8.54a6 6 0 0 0-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 0 0-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 0 1-2.448-2.448 14.9 14.9 0 0 1 .06-.312m-2.24 2.39a4.493 4.493 0 0 0-1.757 4.306 4.493 4.493 0 0 0 4.306-1.758M16.5 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" />''',

        # Device phone mobile (outline) - for mobile apps
        "device-phone-mobile": '''<path stroke-linecap="round" stroke-linejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 0 0 6 3.75v16.5a2.25 2.25 0 0 0 2.25 2.25h7.5A2.25 2.25 0 0 0 18 20.25V3.75a2.25 2.25 0 0 0-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3" />''',

        # Puzzle piece (outline) - for extensions
        "puzzle-piece": '''<path stroke-linecap="round" stroke-linejoin="round" d="M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 0 1-.657.643 48.39 48.39 0 0 1-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 0 1-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 0 0-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 0 1-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 0 0 .657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 0 1-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.4.604-.4.959v0c0 .333.277.599.61.58a48.1 48.1 0 0 0 5.427-.63 48.05 48.05 0 0 0 .582-4.717.532.532 0 0 0-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.959.401v0a.656.656 0 0 0 .659-.663 47.703 47.703 0 0 0-.31-4.82 48.847 48.847 0 0 1-6.067.21.64.64 0 0 1-.657-.643v0Z" />''',

        # Apple logo (solid) - brand icon
        "apple": '''<path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11Z"/>''',

        # Android logo (solid) - brand icon
        "android": '''<path d="M6 18c0 .55.45 1 1 1h1v3.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V19h2v3.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V19h1c.55 0 1-.45 1-1V8H6v10zM3.5 8C2.67 8 2 8.67 2 9.5v7c0 .83.67 1.5 1.5 1.5S5 17.33 5 16.5v-7C5 8.67 4.33 8 3.5 8zm17 0c-.83 0-1.5.67-1.5 1.5v7c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5v-7c0-.83-.67-1.5-1.5-1.5zm-4.97-5.84l1.3-1.3c.2-.2.2-.51 0-.71-.2-.2-.51-.2-.71 0l-1.48 1.48C13.85 1.23 12.95 1 12 1c-.96 0-1.86.23-2.66.63L7.85.15c-.2-.2-.51-.2-.71 0-.2.2-.2.51 0 .71l1.31 1.31C6.97 3.26 6 5.01 6 7h12c0-1.99-.97-3.75-2.47-4.84zM10 5H9V4h1v1zm5 0h-1V4h1v1z"/>''',

        # Google logo (solid) - brand icon
        "google": '''<path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />''',

        # GitHub logo (solid) - brand icon
        "github": '''<path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>''',

        # Book open (outline) - for documentation
        "book-open": '''<path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />''',

        # Key (outline) - for authentication
        "key": '''<path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />''',

        # Exclamation triangle (outline) - for warnings/errors
        "exclamation-triangle": '''<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />''',

        # Clock (outline) - for rate limits/time
        "clock": '''<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />''',

        # Arrow down tray (outline) - for download/export
        "arrow-down-tray": '''<path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />''',

        # Clipboard document check (outline) - for copy
        "clipboard-document-check": '''<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z" />''',

        # Check (outline) - for success states
        "check": '''<path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />''',
    }

    path_content = icons.get(name, icons["bookmark"])

    # Determine if it's a solid or outline icon (solid icons use fill, outline use stroke)
    is_solid = name in ["bookmark", "apple", "android", "google", "github"]

    all_classes = f"{size} {cls}".strip()

    if is_solid:
        return NotStr(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="{all_classes}">{path_content}</svg>''')
    else:
        return NotStr(f'''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="{all_classes}">{path_content}</svg>''')


# =============================================================================
# Page Layout Components
# =============================================================================

def page_head(title: str = "ClipJot"):
    """Generate page head with CSS/JS dependencies."""
    # Google Analytics (if configured)
    ga_elements = ()
    if config.GOOGLE_ANALYTICS_ID:
        ga_elements = (
            Script(src=f"https://www.googletagmanager.com/gtag/js?id={config.GOOGLE_ANALYTICS_ID}", async_=True),
            Script(f"""
                window.dataLayer = window.dataLayer || [];
                function gtag(){{dataLayer.push(arguments);}}
                gtag('js', new Date());
                gtag('config', '{config.GOOGLE_ANALYTICS_ID}');
            """),
        )

    return (
        *ga_elements,
        Title(title),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        # Favicon and PWA
        Link(rel="icon", type="image/png", href="/static/favicon.png"),
        Link(rel="apple-touch-icon", href="/static/apple-touch-icon.png"),
        Link(rel="manifest", href="/static/manifest.json"),
        Meta(name="theme-color", content="#6366f1"),
        # DaisyUI + Tailwind CSS
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css"),
        Script(src="https://cdn.tailwindcss.com"),
        # Custom DaisyUI theme colors via CSS variables (OKLCH format for DaisyUI 4)
        Style("""
            :root, [data-theme="light"], [data-theme="dark"] {
                --p: 0.5457 0.2118 264.05;  /* #6366f1 indigo */
                --pf: 0.4958 0.2044 265.75; /* #4f46e5 darker indigo */
                --pc: 1 0 0;                 /* white */
            }
        """),
        # HTMX
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        # Dark mode script
        Script("""
            // Apply dark mode based on system preference
            if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.documentElement.setAttribute('data-theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
            }
            // Listen for changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            });
        """),
        # URL scheme stripping for mobile
        Style("""
            @media (max-width: 768px) {
                body.strip-url-scheme .url-full { display: none !important; }
                body.strip-url-scheme .url-stripped { display: inline !important; }
            }
        """),
        Script("""
            // Strip URL scheme setting (default: enabled)
            document.addEventListener('DOMContentLoaded', function() {
                const enabled = localStorage.getItem('stripUrlScheme') !== 'false';
                if (enabled) {
                    document.body.classList.add('strip-url-scheme');
                }
            });
        """),
    )


def page_layout(content, title: str = "ClipJot", user: Optional[User] = None, flash: Optional[str] = None, hide_login: bool = False):
    """Wrap content in full page layout with navbar and footer."""
    main_children = [content]
    if flash:
        main_children.insert(0, flash_message(flash))

    return Html(
        Head(*page_head(title)),
        Body(
            navbar(user, hide_login=hide_login),
            Main(
                *main_children,
                cls="container mx-auto px-4 py-6 max-w-6xl",
            ),
            Footer(
                P(
                    "© 2025 ",
                    A("RingZero LLC", href="https://ringzero.ai", cls="hover:underline", target="_blank"),
                    Span(" · ", cls="mx-1"),
                    A("Privacy Policy", href="/privacy", cls="hover:underline"),
                    Span(" · ", cls="mx-1"),
                    A("Developers", href="/docs/api", cls="hover:underline"),
                    cls="text-base-content/50 text-sm",
                ),
                cls="py-8 text-center",
            ),
            keyboard_shortcuts_script(),
            cls="min-h-screen bg-base-200",
        ),
        lang="en",
    )


def navbar(user: Optional[User] = None, hide_login: bool = False):
    """Navigation bar component."""
    search_form = Form(
        Div(
            Input(
                type="search",
                name="q",
                placeholder="Search...",
                cls="input input-bordered w-48 md:w-64 pr-10",
                id="search-input",
            ),
            Kbd("/", cls="kbd kbd-sm absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none", id="search-hint"),
            cls="relative",
        ),
        Script("""
            const si = document.getElementById('search-input');
            const hint = document.getElementById('search-hint');
            function updateHint() { hint.style.display = si.value ? 'none' : ''; }
            si.addEventListener('input', updateHint);
            si.addEventListener('focus', () => hint.style.display = 'none');
            si.addEventListener('blur', updateHint);
            updateHint();
        """),
        cls="form-control" if user else "hidden",
        action="/",
        method="get",
    )

    return Nav(
        Div(
            A(
                heroicon("bookmark", "w-6 h-6 shrink-0", "text-indigo-500"),
                "ClipJot",
                href="/",
                cls="btn btn-ghost text-xl gap-2",
            ),
            cls="flex-1",
        ),
        Div(
            search_form,
            user_menu(user) if user else (None if hide_login else login_button()),
            cls="flex-none gap-2",
        ),
        cls="navbar bg-base-100 shadow-lg",
    )


def user_menu(user: User):
    """User dropdown menu."""
    menu_items = [
        Li(A("My Links", href="/")),
        Li(A("Settings", href="/settings")),
        Li(A("Manage Tags", href="/settings/tags")),
        Li(A("API Tokens", href="/settings/tokens")),
        Li(A("Sessions", href="/settings/sessions")),
        Li(A("Export Data", href="/export")),
        Hr(cls="my-1"),
    ]
    if user.is_admin:
        menu_items.append(Li(A("Admin", href="/admin")))
    menu_items.append(Li(A("Sign Out", href="/logout", hx_post="/logout", hx_swap="none")))

    return Div(
        Div(
            Div(
                Span(user.email[0].upper(), cls="text-xl"),
                cls="bg-neutral text-neutral-content rounded-full w-10",
            ),
            tabindex="0",
            role="button",
            cls="btn btn-ghost btn-circle avatar placeholder",
        ),
        Ul(
            *menu_items,
            tabindex="0",
            cls="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52",
        ),
        cls="dropdown dropdown-end",
    )


def login_button():
    """Sign in button for unauthenticated users."""
    return A("Sign In", href="/login", cls="btn btn-primary")


def landing_hero():
    """Hero section for landing page."""
    return Div(
        Div(
            # App icon and name
            Div(
                Div(
                    heroicon("bookmark", "w-14 h-14", "text-indigo-500"),
                    H1("ClipJot", cls="text-5xl font-bold"),
                    cls="flex items-center justify-center gap-3",
                ),
                P("Your Personal Link Manager", cls="text-xl text-base-content/70 mt-2"),
                cls="text-center",
            ),
            # Description
            P(
                "Save links from anywhere and access them from any device. "
                "Organize with tags, add notes, and never lose a link again.",
                cls="text-center text-lg text-base-content/80 max-w-2xl mx-auto mt-6",
            ),
            # CTA Button
            Div(
                A(
                    "Sign In to Get Started",
                    href="/login",
                    cls="btn btn-primary btn-lg",
                ),
                cls="text-center mt-8",
            ),
            cls="py-16 px-4",
        ),
        cls="bg-base-100 rounded-lg shadow-xl",
    )


def landing_features():
    """Features section for landing page."""
    features = [
        {
            "icon": "rocket-launch",
            "title": "Your Data Belongs to You",
            "description": "Full API access lets you export, automate, and build on top of your data however you want.",
        },
        {
            "icon": "share",
            "title": "Save From Anywhere",
            "description": "Use the browser extension, mobile app, or share from any app to save links instantly.",
        },
        {
            "icon": "tag",
            "title": "Organize With Tags",
            "description": "Create custom tags to categorize your links and find them quickly.",
        },
        {
            "icon": "globe-alt",
            "title": "Access Everywhere",
            "description": "Your links sync across all your devices — web, Chrome, and Android.",
        },
    ]

    feature_cards = [
        Div(
            Div(
                Div(
                    heroicon(f["icon"], "w-8 h-8", "text-primary"),
                    cls="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mb-4",
                ),
                H3(f["title"], cls="text-lg font-semibold mb-2"),
                P(f["description"], cls="text-base-content/70"),
                cls="card-body items-center text-center",
            ),
            cls="card bg-base-100 shadow-md",
        )
        for f in features
    ]

    return Div(
        H2("Why ClipJot?", cls="text-2xl font-bold text-center mb-8"),
        Div(
            *feature_cards,
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6",
        ),
        cls="py-12 px-4",
    )


def landing_downloads():
    """Download/install section for landing page."""
    platforms = [
        {
            "icon": "apple",
            "title": "iOS",
            "description": "Download from the App Store",
            "link": "https://apps.apple.com/app/clipjot",  # TODO: Update with real link
            "link_text": "App Store",
        },
        {
            "icon": "android",
            "title": "Android",
            "description": "Download the APK from GitHub",
            "link": "https://github.com/anthropics/clipjot-android/releases",  # TODO: Update with real link
            "link_text": "GitHub Releases",
        },
        {
            "icon": "puzzle-piece",
            "title": "Chrome Extension",
            "description": "Install from GitHub",
            "link": "https://github.com/anthropics/clipjot-chrome",  # TODO: Update with real link
            "link_text": "GitHub",
        },
    ]

    platform_cards = [
        Div(
            Div(
                Div(
                    heroicon(p["icon"], "w-8 h-8", "text-primary"),
                    cls="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mb-4",
                ),
                H3(p["title"], cls="text-lg font-semibold mb-2"),
                P(p["description"], cls="text-base-content/70 mb-4"),
                A(
                    p["link_text"],
                    href=p["link"],
                    cls="btn btn-primary btn-sm",
                    target="_blank",
                ),
                cls="card-body items-center text-center",
            ),
            cls="card bg-base-100 shadow-md",
        )
        for p in platforms
    ]

    return Div(
        H2("Get ClipJot", cls="text-2xl font-bold text-center mb-8"),
        Div(
            *platform_cards,
            cls="grid grid-cols-1 md:grid-cols-3 gap-6",
        ),
        cls="py-12 px-4",
    )


def settings_nav(current: str = None):
    """Navigation links for settings pages.

    Args:
        current: The current page identifier to highlight (e.g., 'links', 'settings', 'tags', 'tokens', 'sessions', 'export')
    """
    links = [
        ("links", "My Links", "/"),
        ("settings", "Settings", "/settings"),
        ("tags", "Manage Tags", "/settings/tags"),
        ("tokens", "API Tokens", "/settings/tokens"),
        ("sessions", "Sessions", "/settings/sessions"),
        ("export", "Export Data", "/export"),
    ]

    buttons = []
    for key, label, href in links:
        cls = "btn btn-primary" if key == current else "btn btn-outline"
        buttons.append(A(label, href=href, cls=cls))

    return Div(
        *buttons,
        cls="flex flex-wrap gap-4 mt-8 pt-6 border-t border-base-300",
    )


# =============================================================================
# Flash Messages
# =============================================================================

def flash_message(message: str, type: str = "info"):
    """Display a flash message."""
    alert_class = {
        "success": "alert-success",
        "error": "alert-error",
        "warning": "alert-warning",
        "info": "alert-info",
    }.get(type, "alert-info")

    return Div(
        Span(message),
        Button(
            heroicon("x-mark", "w-4 h-4"),
            cls="btn btn-sm btn-ghost btn-square",
            onclick="this.parentElement.remove()",
        ),
        cls=f"alert {alert_class} mb-4",
    )


# =============================================================================
# Bookmark Components
# =============================================================================

def strip_url_scheme(url: str) -> str:
    """Strip http:// or https:// from URL for display."""
    if url:
        if url.startswith("https://"):
            return url[8:]
        elif url.startswith("http://"):
            return url[7:]
    return url


def truncate_text(text: str, max_length: int = 80) -> str:
    """Truncate text to max_length characters, adding ellipsis if truncated."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def bookmark_row(bookmark: Bookmark, tags: list[Tag], selected: bool = False):
    """Single bookmark row in list view."""
    domain = urlparse(bookmark.url).netloc if bookmark.url else ""

    tag_elements = [tag_chip(t) for t in tags[:5]]
    if len(tags) > 5:
        tag_elements.append(Span(f"+{len(tags) - 5}", cls="badge badge-sm"))

    # If no title, use URL (with scheme stripped for mobile via CSS/JS)
    if bookmark.title:
        full_title = bookmark.title
        display_title = truncate_text(bookmark.title, 80)
        is_url_as_title = False
    else:
        full_title = bookmark.url
        display_title = truncate_text(bookmark.url, 80)
        is_url_as_title = True

    # Show full title on hover if truncated
    hover_title = full_title if full_title != display_title else bookmark.url

    return Tr(
        # Checkbox
        Td(
            Input(
                type="checkbox",
                cls="checkbox checkbox-sm bookmark-checkbox",
                name="selected",
                value=str(bookmark.id),
                checked=selected,
            ),
            cls="w-8 px-1",
        ),
        # Title & URL
        Td(
            Div(
                A(
                    # Show full URL, but include stripped version for mobile
                    Span(display_title, cls="url-full") if is_url_as_title else display_title,
                    Span(truncate_text(strip_url_scheme(bookmark.url), 80), cls="url-stripped hidden") if is_url_as_title else None,
                    href=bookmark.url,
                    target="_blank",
                    cls="link link-primary font-medium break-all",
                    title=hover_title,
                ),
                Button(
                    heroicon("pencil-square", "w-4 h-4", "text-base-content/60 hover:text-primary"),
                    cls="ml-1 flex-shrink-0 hover:scale-110 transition-transform btn btn-ghost btn-xs p-0",
                    title=bookmark.comment,
                    hx_get=f"/bookmarks/{bookmark.id}/edit",
                    hx_target="#modal-container",
                ) if bookmark.comment else None,
                cls="flex items-start",
            ),
            Span(domain, cls="text-xs text-base-content/60 break-all"),
            cls="px-1",
        ),
        # Tags (hidden on mobile)
        Td(
            Div(*tag_elements, cls="flex flex-wrap gap-1"),
            cls="hidden md:table-cell px-1",
        ),
        # Date (hidden on mobile)
        Td(
            Span(
                format_date(bookmark.created_at),
                cls="text-sm text-base-content/70",
                title=bookmark.created_at,
            ),
            cls="hidden md:table-cell px-1",
        ),
        # Actions
        Td(
            Button(
                heroicon("clipboard-document", "w-4 h-4"),
                cls="btn btn-xs btn-ghost btn-square copy-btn",
                title="Copy URL",
                data_url=bookmark.url,
                data_title=bookmark.title or bookmark.url,
                onclick="copyBookmark(this)",
            ),
            Button(
                heroicon("pencil", "w-4 h-4"),
                cls="btn btn-xs btn-ghost btn-square",
                title="Edit",
                hx_get=f"/bookmarks/{bookmark.id}/edit",
                hx_target="#modal-container",
            ),
            cls="w-20 px-1 flex gap-1",
        ),
        cls="hover",
        id=f"bookmark-{bookmark.id}",
        data_bookmark_id=str(bookmark.id),
    )


def bookmark_list(bookmarks: list[tuple[Bookmark, list[Tag]]], selected_ids: set[int] = None):
    """Table of bookmarks."""
    if selected_ids is None:
        selected_ids = set()

    rows = [bookmark_row(b, tags, b.id in selected_ids) for b, tags in bookmarks]

    return Table(
        Thead(
            Tr(
                Th(
                    Input(
                        type="checkbox",
                        cls="checkbox checkbox-sm",
                        id="select-all",
                        onclick="toggleAllBookmarks(this)",
                    ),
                    cls="w-8 px-1",
                ),
                Th("Link", cls="px-1"),
                Th("Tags", cls="hidden md:table-cell px-1"),
                Th("Added", cls="hidden md:table-cell px-1"),
                Th("", cls="w-10 px-1"),  # Actions column, no header text
            )
        ),
        Tbody(*rows, id="bookmark-list"),
        cls="table table-zebra table-sm w-full",
    )


def bookmark_form(bookmark: Optional[Bookmark] = None, tags: list[Tag] = None, all_tags: list[Tag] = None):
    """Form for adding/editing a bookmark."""
    is_edit = bookmark is not None
    action = f"/bookmarks/{bookmark.id}" if is_edit else "/bookmarks/add"

    # Build comma-separated tag names for existing tags
    existing_tag_names = ", ".join(t.name for t in (tags or []))
    # Build list of all available tag names for autocomplete
    available_tags = [t.name for t in (all_tags or [])]

    # Autocomplete JS with keyboard navigation
    tag_autocomplete_js = """
    (function() {
        const input = document.getElementById('tag-input');
        const suggestions = document.getElementById('tag-suggestions');
        const availableTags = window.availableTags || [];
        let selectedIndex = -1;
        let currentMatches = [];

        function getCurrentWord() {
            const value = input.value;
            const lastComma = value.lastIndexOf(',');
            return value.substring(lastComma + 1).trim().toLowerCase();
        }

        function getExistingTags() {
            return input.value.split(',').map(t => t.trim().toLowerCase()).filter(t => t);
        }

        function updateHighlight() {
            const items = suggestions.querySelectorAll('.suggestion-item');
            items.forEach((item, i) => {
                if (i === selectedIndex) {
                    item.classList.add('bg-primary', 'text-primary-content');
                    item.classList.remove('hover:bg-base-200');
                } else {
                    item.classList.remove('bg-primary', 'text-primary-content');
                    item.classList.add('hover:bg-base-200');
                }
            });
        }

        function showSuggestions() {
            const currentWord = getCurrentWord();
            const existingTags = getExistingTags();

            if (currentWord.length === 0) {
                suggestions.classList.add('hidden');
                currentMatches = [];
                selectedIndex = -1;
                return;
            }

            currentMatches = availableTags.filter(t =>
                t.toLowerCase().includes(currentWord) &&
                !existingTags.includes(t.toLowerCase())
            ).slice(0, 8);

            if (currentMatches.length > 0) {
                suggestions.innerHTML = currentMatches.map((t, i) =>
                    '<div class="suggestion-item px-3 py-2 hover:bg-base-200 cursor-pointer" data-index="' + i + '" onclick="selectTag(\\'' + t.replace(/'/g, "\\\\'") + '\\')">' + t + '</div>'
                ).join('');
                suggestions.classList.remove('hidden');
                selectedIndex = -1;
            } else {
                suggestions.classList.add('hidden');
                currentMatches = [];
                selectedIndex = -1;
            }
        }

        input.addEventListener('input', showSuggestions);

        input.addEventListener('keydown', function(e) {
            if (suggestions.classList.contains('hidden') || currentMatches.length === 0) {
                return;
            }

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % currentMatches.length;
                updateHighlight();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = selectedIndex <= 0 ? currentMatches.length - 1 : selectedIndex - 1;
                updateHighlight();
            } else if (e.key === 'Enter') {
                if (selectedIndex >= 0 && selectedIndex < currentMatches.length) {
                    e.preventDefault();
                    selectTag(currentMatches[selectedIndex]);
                }
            } else if (e.key === 'Escape') {
                suggestions.classList.add('hidden');
                selectedIndex = -1;
            }
        });

        input.addEventListener('blur', function() {
            setTimeout(() => {
                suggestions.classList.add('hidden');
                selectedIndex = -1;
            }, 150);
        });

        input.addEventListener('focus', function() {
            if (getCurrentWord().length > 0) {
                showSuggestions();
            }
        });
    })();

    function selectTag(tag) {
        const input = document.getElementById('tag-input');
        const suggestions = document.getElementById('tag-suggestions');
        const value = input.value;
        const lastComma = value.lastIndexOf(',');
        const prefix = lastComma >= 0 ? value.substring(0, lastComma + 1) + ' ' : '';
        input.value = prefix + tag + ', ';
        suggestions.classList.add('hidden');
        input.focus();
    }
    """

    return Form(
        # URL (read-only on edit)
        Div(
            Label("URL", cls="label", for_="url"),
            Input(
                type="url",
                name="url",
                id="url",
                value=bookmark.url if bookmark else "",
                required=True,
                readonly=is_edit,
                cls="input input-bordered" + (" input-disabled" if is_edit else ""),
                placeholder="https://example.com",
            ),
            cls="form-control",
        ),
        # Title
        Div(
            Label("Title", cls="label", for_="title"),
            Input(
                type="text",
                name="title",
                id="title",
                value=bookmark.title if bookmark else "",
                cls="input input-bordered",
                placeholder="Page title",
            ),
            cls="form-control",
        ),
        # Tags with autocomplete
        Div(
            Label("Tags", cls="label", for_="tag-input"),
            Div(
                Input(
                    type="text",
                    name="tags",
                    id="tag-input",
                    value=existing_tag_names,
                    cls="input input-bordered w-full",
                    placeholder="Enter tags separated by commas",
                    autocomplete="off",
                ),
                Div(
                    id="tag-suggestions",
                    cls="hidden absolute z-50 w-full mt-1 bg-base-100 border border-base-300 rounded-lg shadow-lg max-h-48 overflow-y-auto",
                ),
                cls="relative",
            ),
            Script(f"window.availableTags = {json.dumps(available_tags)};"),
            Script(tag_autocomplete_js),
            cls="form-control",
        ),
        # Comment
        Div(
            Label("Comment", cls="label", for_="comment"),
            Textarea(
                bookmark.comment if bookmark else "",
                name="comment",
                id="comment",
                cls="textarea textarea-bordered",
                placeholder="Add a note...",
                rows="3",
            ),
            cls="form-control",
        ),
        # Submit
        Div(
            Button("Cancel", type="button", cls="btn btn-ghost", onclick="closeModal()"),
            Button(
                "Save" if is_edit else "Add Link",
                type="submit",
                cls="btn btn-primary",
            ),
            cls="flex justify-end gap-2",
        ),
        # Auto-focus the appropriate field when modal loads
        Script(f"document.getElementById('{'title' if is_edit else 'url'}').focus();"),
        cls="space-y-4",
        action=action,
        method="post",
        hx_post=action,
        hx_swap="outerHTML",
    )


# =============================================================================
# Tag Components
# =============================================================================

def tag_chip(tag: Tag, removable: bool = False, bookmark_id: Optional[int] = None):
    """Display a tag as a chip."""
    children = [tag.name]
    if removable and bookmark_id:
        children.append(
            Button(
                heroicon("x-mark", "w-3 h-3"),
                cls="btn btn-xs btn-ghost p-0 min-h-0 h-4 w-4",
                hx_delete=f"/bookmarks/{bookmark_id}/tags/{tag.id}",
                hx_swap="outerHTML",
            )
        )

    return Span(
        *children,
        cls="badge badge-primary gap-1",
        style="padding: 0.25rem 0.625rem; height: auto;",
    )


def tag_list_item(tag: dict):
    """Tag item in settings list (with count)."""
    return Tr(
        Td(Span(tag["name"], cls="font-medium")),
        Td(Span(f"{tag['bookmark_count']} bookmarks", cls="text-sm text-base-content/70")),
        Td(
            Div(
                Button(
                    "Delete",
                    cls="btn btn-xs btn-ghost text-error",
                    hx_delete=f"/settings/tags/{tag['id']}",
                    hx_confirm=f"Delete tag '{tag['name']}'? It will be removed from all bookmarks.",
                    hx_target=f"#tag-{tag['id']}",
                    hx_swap="outerHTML",
                ),
                cls="flex gap-1",
            )
        ),
        id=f"tag-{tag['id']}",
    )


# =============================================================================
# Pagination
# =============================================================================

def pagination(page: int, total: int, per_page: int, base_url: str = "/"):
    """Pagination component."""
    total_pages = (total + per_page - 1) // per_page
    if total_pages <= 1:
        return None

    # Build page range
    start = max(1, page - 2)
    end = min(total_pages, page + 2)

    pages = []
    if start > 1:
        pages.append(1)
        if start > 2:
            pages.append("...")
    pages.extend(range(start, end + 1))
    if end < total_pages:
        if end < total_pages - 1:
            pages.append("...")
        pages.append(total_pages)

    def page_link(p):
        if p == "...":
            return Span("...", cls="px-2")
        url = f"{base_url}?page={p}" if "?" not in base_url else f"{base_url}&page={p}"
        return A(
            str(p),
            href=url,
            cls=f"btn btn-sm {'btn-active' if p == page else ''}",
        )

    children = []
    if page > 1:
        children.append(A("Prev", href=f"{base_url}?page={page-1}", cls="btn btn-sm", id="page-prev"))
    children.extend([page_link(p) for p in pages])
    if page < total_pages:
        children.append(A("Next", href=f"{base_url}?page={page+1}", cls="btn btn-sm", id="page-next"))

    return Div(*children, cls="flex justify-center gap-1 mt-6")


# =============================================================================
# Modal Components
# =============================================================================

def modal_container():
    """Container for HTMX-loaded modals."""
    return Div(id="modal-container")


def modal(title: str, content, id: str = "modal"):
    """Modal dialog."""
    return Div(
        Div(
            H3(title, cls="font-bold text-lg mb-4"),
            content,
            cls="modal-box",
        ),
        Div(cls="modal-backdrop", onclick="closeModal()"),
        cls="modal modal-open",
        id=id,
    )


def keyboard_help_hint():
    """Hint about keyboard shortcuts at bottom of page."""
    return Div(
        Span("Press "),
        Kbd("?", cls="kbd kbd-sm"),
        Span(" for keyboard shortcuts"),
        cls="text-center text-sm text-base-content/50 mt-8 mb-4",
    )


def new_links_banner(latest_bookmark_id: int | None, last_updated: str | None = None):
    """Banner that shows when new links are available or edited, with polling script."""
    # JSON-safe string for last_updated (null or quoted string)
    last_updated_js = f'"{last_updated}"' if last_updated else 'null'

    return Div(
        # Hidden banner - shown by JavaScript when new/edited links detected
        Div(
            Span("Links updated"),
            Button(
                "Refresh",
                cls="btn btn-sm btn-primary ml-2",
                onclick="window.location.reload()",
            ),
            Button(
                heroicon("x-mark", "w-4 h-4"),
                cls="btn btn-sm btn-ghost btn-square ml-1",
                onclick="this.parentElement.classList.add('hidden')",
            ),
            cls="alert alert-info hidden flex-row justify-center items-center mb-4",
            id="new-links-banner",
        ),
        # Polling script with visibility detection
        Script(f"""
            (function() {{
                const latestId = {latest_bookmark_id if latest_bookmark_id else 'null'};
                const lastUpdated = {last_updated_js};
                if (!latestId) return;  // No bookmarks yet

                const pollInterval = 60000;  // 60 seconds
                let pollTimer = null;

                function hasChanges(data) {{
                    // Check for new bookmarks (higher ID)
                    const hasNewBookmark = data.id && data.id > latestId;
                    // Check for edits (different timestamp)
                    const hasUpdates = lastUpdated && data.last_updated && data.last_updated !== lastUpdated;
                    return hasNewBookmark || hasUpdates;
                }}

                async function checkForNewLinks() {{
                    try {{
                        const response = await fetch('/api/internal/latest-bookmark');
                        if (!response.ok) return;
                        const data = await response.json();
                        if (hasChanges(data)) {{
                            document.getElementById('new-links-banner')?.classList.remove('hidden');
                        }}
                    }} catch (e) {{
                        // Silently ignore errors
                    }}
                }}

                function startPolling() {{
                    if (!pollTimer) {{
                        pollTimer = setInterval(checkForNewLinks, pollInterval);
                    }}
                }}

                function stopPolling() {{
                    if (pollTimer) {{
                        clearInterval(pollTimer);
                        pollTimer = null;
                    }}
                }}

                // Handle tab visibility changes
                document.addEventListener('visibilitychange', async function() {{
                    if (document.hidden) {{
                        stopPolling();
                    }} else {{
                        // Check for changes when tab becomes visible and auto-refresh if found
                        try {{
                            const response = await fetch('/api/internal/latest-bookmark');
                            if (response.ok) {{
                                const data = await response.json();
                                if (hasChanges(data)) {{
                                    // Auto-refresh to show changes
                                    window.location.reload();
                                    return;
                                }}
                            }}
                        }} catch (e) {{
                            // Silently ignore errors
                        }}
                        startPolling();
                    }}
                }});

                // Start polling only if page is visible
                if (!document.hidden) {{
                    startPolling();
                }}
            }})();
        """),
        id="new-links-checker",
    )


# =============================================================================
# Bulk Operations
# =============================================================================

def bulk_actions_bar():
    """Toolbar for bulk bookmark operations."""
    return Div(
        Span(cls="mr-4", id="selected-count"),
        Button(
            "Delete Selected",
            cls="btn btn-sm btn-error mr-2",
            hx_delete="/bookmarks/bulk",
            hx_include="[name='selected']:checked",
            hx_confirm="Delete selected links?",
        ),
        Button(
            "Add Tag",
            cls="btn btn-sm btn-ghost mr-2",
            hx_post="/bookmarks/bulk/add-tag",
            hx_include="[name='selected']:checked",
            hx_target="#modal-container",
        ),
        Button(
            "Remove Tag",
            cls="btn btn-sm btn-ghost",
            hx_post="/bookmarks/bulk/remove-tag",
            hx_include="[name='selected']:checked",
            hx_target="#modal-container",
        ),
        cls="bg-base-100 p-3 rounded-lg shadow mb-4 hidden",
        id="bulk-actions",
    )


# =============================================================================
# Keyboard Shortcuts
# =============================================================================

def keyboard_shortcuts_script():
    """JavaScript for vim-style keyboard navigation."""
    return Script("""
        // Focus search field if #search hash is present
        if (window.location.hash === '#search') {
            document.getElementById('search-input')?.focus();
            history.replaceState(null, '', window.location.pathname);
        }

        let currentIndex = -1;
        const rows = () => document.querySelectorAll('#bookmark-list tr');

        function selectRow(index) {
            const r = rows();
            if (currentIndex >= 0 && currentIndex < r.length) {
                r[currentIndex].style.outline = '';
                r[currentIndex].style.outlineOffset = '';
            }
            currentIndex = Math.max(0, Math.min(index, r.length - 1));
            if (currentIndex >= 0 && currentIndex < r.length) {
                r[currentIndex].style.outline = '2px solid oklch(var(--p))';
                r[currentIndex].style.outlineOffset = '-2px';
                r[currentIndex].scrollIntoView({block: 'nearest'});
            }
        }

        function toggleSelection() {
            const r = rows();
            if (currentIndex >= 0 && currentIndex < r.length) {
                const cb = r[currentIndex].querySelector('.bookmark-checkbox');
                if (cb) cb.checked = !cb.checked;
                updateBulkBar();
            }
        }

        function toggleAllBookmarks(el) {
            document.querySelectorAll('.bookmark-checkbox').forEach(cb => cb.checked = el.checked);
            updateBulkBar();
        }

        function updateBulkBar() {
            const checked = document.querySelectorAll('.bookmark-checkbox:checked').length;
            const bar = document.getElementById('bulk-actions');
            const count = document.getElementById('selected-count');
            if (checked > 0) {
                bar.classList.remove('hidden');
                count.textContent = checked + ' selected';
            } else {
                bar.classList.add('hidden');
            }
        }

        function closeModal() {
            const modal = document.querySelector('.modal');
            if (modal) modal.remove();
        }

        function showKeyboardHelp() {
            const shortcuts = [
                ['a', 'Add new link'],
                ['/', 'Focus search / Clear search'],
                ['j / k', 'Navigate down / up'],
                ['gg / G', 'Go to first / last row'],
                ['n / p', 'Next / Previous page'],
                ['Enter', 'Open selected link'],
                ['o', 'Open in new tab'],
                ['x', 'Toggle checkbox'],
                ['Escape', 'Close modal / Clear selection'],
                ['?', 'Show this help'],
            ];
            const rows = shortcuts.map(([key, desc]) =>
                `<tr><td><kbd class="kbd kbd-sm">${key}</kbd></td><td class="pl-4">${desc}</td></tr>`
            ).join('');
            const modal = document.createElement('div');
            modal.className = 'modal modal-open';
            modal.id = 'keyboard-help';
            modal.innerHTML = `
                <div class="modal-box">
                    <h3 class="font-bold text-lg mb-4">Keyboard Shortcuts</h3>
                    <table class="table table-sm"><tbody>${rows}</tbody></table>
                    <div class="modal-action"><button class="btn" onclick="closeModal()">Close</button></div>
                </div>
                <div class="modal-backdrop" onclick="closeModal()"></div>
            `;
            document.body.appendChild(modal);
        }

        // Track last key press for gg detection
        let lastKeyTime = 0;
        let lastKey = '';

        document.addEventListener('keydown', (e) => {
            // Escape always works - close modal even when in input
            if (e.key === 'Escape') {
                const modal = document.querySelector('.modal');
                if (modal) {
                    e.preventDefault();
                    closeModal();
                    return;
                }
                // If no modal, clear selections
                document.querySelectorAll('.bookmark-checkbox').forEach(cb => cb.checked = false);
                updateBulkBar();
                return;
            }

            // Skip other shortcuts if in input/textarea
            if (e.target.matches('input, textarea, select')) return;

            const now = Date.now();

            switch(e.key) {
                case 'a':
                    // Add new link - trigger the add link button
                    const addBtn = document.querySelector('[hx-get="/bookmarks/add"]');
                    if (addBtn) {
                        e.preventDefault();
                        addBtn.click();
                    }
                    break;
                case '/':
                    e.preventDefault();
                    const searchInput = document.getElementById('search-input');
                    if (searchInput) {
                        // If there's a search query active, clear and go to full list with focus
                        if (window.location.search.includes('q=')) {
                            window.location.href = '/#search';
                        } else {
                            searchInput.focus();
                        }
                    }
                    break;
                case 'j':
                    selectRow(currentIndex + 1);
                    break;
                case 'k':
                    selectRow(currentIndex - 1);
                    break;
                case 'x':
                    toggleSelection();
                    break;
                case 'Enter':
                case 'o':
                    const r = rows();
                    if (currentIndex >= 0 && currentIndex < r.length) {
                        const link = r[currentIndex].querySelector('a');
                        if (link) {
                            if (e.key === 'o') window.open(link.href, '_blank');
                            else window.location = link.href;
                        }
                    }
                    break;
                case 'g':
                    if (e.shiftKey) {
                        selectRow(rows().length - 1);
                    } else {
                        // gg - go to first row (double-tap within 500ms)
                        if (lastKey === 'g' && now - lastKeyTime < 500) {
                            selectRow(0);
                            lastKey = '';  // Reset to prevent triple-g issues
                        }
                    }
                    break;
                case 'n':
                    const nextPage = document.getElementById('page-next');
                    if (nextPage) window.location.href = nextPage.href;
                    break;
                case 'p':
                    const prevPage = document.getElementById('page-prev');
                    if (prevPage) window.location.href = prevPage.href;
                    break;
                case 'G':
                    selectRow(rows().length - 1);
                    break;
                case '?':
                    showKeyboardHelp();
                    break;
            }

            // Track last key for double-tap detection (gg)
            lastKey = e.key;
            lastKeyTime = now;
        });

        // Update bulk bar when checkboxes change
        document.addEventListener('change', (e) => {
            if (e.target.matches('.bookmark-checkbox')) updateBulkBar();
        });

        // Copy bookmark URL with rich format (HTML link)
        async function copyBookmark(btn) {
            const url = btn.dataset.url;
            const title = btn.dataset.title;
            const htmlContent = `<a href="${url}">${title}</a>`;

            try {
                // Try rich clipboard with both plain text and HTML
                await navigator.clipboard.write([
                    new ClipboardItem({
                        'text/plain': new Blob([url], { type: 'text/plain' }),
                        'text/html': new Blob([htmlContent], { type: 'text/html' })
                    })
                ]);
            } catch (err) {
                // Fallback to plain text only
                await navigator.clipboard.writeText(url);
            }

            // Show brief feedback
            const originalTitle = btn.title;
            btn.title = 'Copied!';
            btn.classList.add('text-success');
            setTimeout(() => {
                btn.title = originalTitle;
                btn.classList.remove('text-success');
            }, 1500);
        }
    """)


# =============================================================================
# Utility Functions
# =============================================================================

def format_date(iso_date: Optional[str]) -> str:
    """Format ISO date for display."""
    if not iso_date:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return iso_date[:10] if iso_date else ""


# =============================================================================
# API Documentation Components
# =============================================================================

def docs_page_layout(content, title: str = "API Documentation - ClipJot", user: Optional[User] = None):
    """Page layout for documentation pages (public, shows profile menu when authenticated)."""
    return Html(
        Head(*page_head(title)),
        Body(
            # Navbar for docs - shows profile menu when authenticated
            Nav(
                Div(
                    A(
                        heroicon("bookmark", "w-6 h-6 shrink-0", "text-indigo-500"),
                        "ClipJot",
                        href="/",
                        cls="btn btn-ghost text-xl gap-2",
                    ),
                    cls="flex-1",
                ),
                Div(
                    A("Docs", href="/docs/api/v1", cls="btn btn-ghost btn-sm"),
                    A("Changelog", href="/docs/api/changelog", cls="btn btn-ghost btn-sm"),
                    user_menu(user) if user else A("Sign In", href="/login", cls="btn btn-primary btn-sm"),
                    cls="flex-none gap-2",
                ),
                cls="navbar bg-base-100 shadow-lg",
            ),
            Main(
                content,
                cls="container mx-auto px-4 py-6 max-w-6xl",
            ),
            Footer(
                P(
                    "© 2025 ",
                    A("RingZero LLC", href="https://ringzero.ai", cls="hover:underline", target="_blank"),
                    Span(" · ", cls="mx-1"),
                    A("Privacy Policy", href="/privacy", cls="hover:underline"),
                    Span(" · ", cls="mx-1"),
                    A("Developers", href="/docs/api", cls="hover:underline"),
                    cls="text-base-content/50 text-sm",
                ),
                cls="py-8 text-center",
            ),
            cls="min-h-screen bg-base-200",
        ),
        lang="en",
    )


def docs_sidebar_nav(sections: list, current_section: str = None):
    """Sidebar navigation for API docs with sticky positioning."""
    nav_items = []
    for section in sections:
        is_active = section["id"] == current_section
        nav_items.append(
            A(
                heroicon(section.get("icon", "book-open"), "w-4 h-4"),
                section["title"],
                href=f"#{ section['id']}",
                cls=f"flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-base-200 {'bg-primary text-primary-content' if is_active else ''}",
            )
        )

    return Div(
        Div(
            H3("On this page", cls="text-sm font-semibold text-base-content/70 mb-3"),
            Nav(*nav_items, cls="flex flex-col gap-1"),
            cls="sticky top-6",
        ),
        cls="hidden lg:block w-48 shrink-0",
    )


def code_example_tabs(examples: dict, endpoint_key: str):
    """Tabbed code examples with copy button."""
    tab_id = f"code-tabs-{endpoint_key.replace('/', '-')}"

    tabs = []
    panels = []

    for i, (lang, code) in enumerate(examples.items()):
        tab_name = {"curl": "cURL", "python": "Python", "javascript": "JavaScript"}.get(lang, lang)
        is_first = i == 0

        tabs.append(
            A(
                tab_name,
                cls=f"tab {'tab-active' if is_first else ''}",
                role="tab",
                data_tab=f"{tab_id}-{lang}",
                onclick=f"switchCodeTab('{tab_id}', '{lang}')",
            )
        )

        panels.append(
            Div(
                Pre(
                    Code(code.strip(), cls=f"language-{lang}"),
                    cls="bg-base-300 p-4 rounded-lg text-sm overflow-x-auto",
                ),
                Button(
                    heroicon("clipboard-document-check", "w-4 h-4"),
                    "Copy",
                    cls="btn btn-xs btn-ghost absolute top-2 right-2",
                    onclick=f"copyCode(this)",
                ),
                id=f"{tab_id}-{lang}",
                cls=f"code-panel relative {'hidden' if not is_first else ''}",
                data_lang=lang,
            )
        )

    return Div(
        Div(*tabs, cls="tabs tabs-boxed mb-2", role="tablist"),
        *panels,
        cls="mt-4",
        id=tab_id,
    )


def schema_table(schema: dict, title: str = "Parameters"):
    """Render a request/response schema as a table."""
    if not schema:
        return None

    rows = []
    for field_name, field_info in schema.items():
        required = field_info.get("required", False)
        field_type = field_info.get("type", "string")
        description = field_info.get("description", "")

        rows.append(
            Tr(
                Td(
                    Code(field_name, cls="text-primary"),
                    Span(" *", cls="text-error") if required else None,
                ),
                Td(Code(field_type, cls="text-xs opacity-70")),
                Td(description, cls="text-sm"),
            )
        )

    return Div(
        H4(title, cls="font-semibold text-sm mb-2"),
        Table(
            Thead(
                Tr(
                    Th("Field", cls="text-left"),
                    Th("Type", cls="text-left"),
                    Th("Description", cls="text-left"),
                )
            ),
            Tbody(*rows),
            cls="table table-xs w-full",
        ),
        cls="mb-4",
    )


def endpoint_doc(endpoint_key: str, endpoint: dict):
    """Document a single API endpoint."""
    method = endpoint.get("method", "POST")
    path = endpoint.get("path", "")
    summary = endpoint.get("summary", "")
    description = endpoint.get("description", "")
    scope = endpoint.get("scope")
    request_schema = endpoint.get("request_schema", {})
    response_schema = endpoint.get("response_schema", {})
    examples = endpoint.get("examples", {})

    # Method badge color
    method_cls = "badge-success" if method == "GET" else "badge-info"

    return Div(
        # Header
        Div(
            Span(method, cls=f"badge {method_cls} font-mono mr-2"),
            Code(path, cls="text-lg font-mono"),
            cls="flex items-center mb-2",
        ),
        # Summary
        P(summary, cls="text-lg font-medium mb-2"),
        # Description
        P(description, cls="text-base-content/70 mb-4") if description != summary else None,
        # Scope badge
        Div(
            Span("Scope: ", cls="text-sm text-base-content/60"),
            Span(scope or "public", cls=f"badge badge-sm {'badge-warning' if scope == 'write' else 'badge-info' if scope == 'read' else 'badge-ghost'}"),
            cls="mb-4",
        ) if scope is not None else Div(
            Span("Public endpoint", cls="text-sm text-base-content/60"),
            cls="mb-4",
        ),
        # Request schema
        schema_table(request_schema, "Request Body") if request_schema else None,
        # Response schema
        schema_table(response_schema, "Response") if response_schema else None,
        # Code examples
        code_example_tabs(examples, endpoint_key) if examples else None,
        cls="card bg-base-100 shadow-md p-6 mb-6",
        id=f"endpoint-{endpoint_key.replace('/', '-')}",
    )


def docs_section(section_id: str, title: str, icon: str, content):
    """A documentation section with anchor."""
    return Section(
        Div(
            heroicon(icon, "w-6 h-6", "text-primary"),
            H2(title, cls="text-2xl font-bold"),
            cls="flex items-center gap-3 mb-6",
        ),
        content,
        id=section_id,
        cls="mb-12 scroll-mt-6",
    )


def landing_developers():
    """Developer section for landing page."""
    return Div(
        H2("For Developers", cls="text-2xl font-bold text-center mb-8"),
        Div(
            Div(
                Div(
                    heroicon("code-bracket", "w-8 h-8", "text-primary"),
                    cls="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mb-4",
                ),
                H3("REST API", cls="text-lg font-semibold mb-2"),
                P(
                    "Full API access to your bookmarks. Build integrations, automate workflows, "
                    "or create your own clients.",
                    cls="text-base-content/70 mb-4"
                ),
                A(
                    "View API Docs",
                    href="/docs/api",
                    cls="btn btn-primary btn-sm",
                ),
                cls="card-body items-center text-center",
            ),
            cls="card bg-base-100 shadow-md max-w-md mx-auto",
        ),
        cls="py-12 px-4",
    )


def docs_code_scripts():
    """JavaScript for code tabs and copy functionality."""
    return Script("""
        function switchCodeTab(tabGroupId, lang) {
            const group = document.getElementById(tabGroupId);
            if (!group) return;

            // Update tab active states
            group.querySelectorAll('.tab').forEach(tab => {
                tab.classList.toggle('tab-active', tab.dataset.tab === tabGroupId + '-' + lang);
            });

            // Show/hide panels
            group.querySelectorAll('.code-panel').forEach(panel => {
                panel.classList.toggle('hidden', panel.dataset.lang !== lang);
            });
        }

        function copyCode(btn) {
            const panel = btn.closest('.code-panel');
            const code = panel.querySelector('code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                const originalText = btn.innerHTML;
                btn.innerHTML = '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg> Copied!';
                btn.classList.add('text-success');
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.classList.remove('text-success');
                }, 2000);
            });
        }
    """)
