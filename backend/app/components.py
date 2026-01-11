"""Reusable FastHTML/FT components for ClipJot UI.

These components provide consistent styling using DaisyUI classes.
"""

import json

from fasthtml.common import *
from typing import Optional
from urllib.parse import urlparse

from .models import Bookmark, Tag, User


# =============================================================================
# Page Layout Components
# =============================================================================

def page_head(title: str = "ClipJot"):
    """Generate page head with CSS/JS dependencies."""
    return (
        Title(title),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        # Favicon
        Link(rel="icon", type="image/png", href="/static/favicon.png"),
        # DaisyUI + Tailwind CSS
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css"),
        Script(src="https://cdn.tailwindcss.com"),
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


def page_layout(content, title: str = "ClipJot", user: Optional[User] = None, flash: Optional[str] = None):
    """Wrap content in full page layout with navbar."""
    main_children = [content]
    if flash:
        main_children.insert(0, flash_message(flash))

    return Html(
        Head(*page_head(title)),
        Body(
            navbar(user),
            Main(
                *main_children,
                cls="container mx-auto px-4 py-6 max-w-6xl",
            ),
            keyboard_shortcuts_script(),
            cls="min-h-screen bg-base-200",
        ),
        lang="en",
    )


def navbar(user: Optional[User] = None):
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
                Img(src="/static/favicon.png", alt="ClipJot", cls="w-6 h-6"),
                "ClipJot",
                href="/",
                cls="btn btn-ghost text-xl gap-2",
            ),
            cls="flex-1",
        ),
        Div(
            search_form,
            user_menu(user) if user else login_button(),
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
        Li(cls="divider"),
    ]
    if user.is_admin:
        menu_items.append(Li(A("Admin", href="/admin")))
    menu_items.append(Li(A("Logout", href="/logout", hx_post="/logout", hx_swap="none")))

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
    """Login button for unauthenticated users."""
    return A("Login", href="/login", cls="btn btn-primary")


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
            "x",
            cls="btn btn-sm btn-ghost",
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


def bookmark_row(bookmark: Bookmark, tags: list[Tag], selected: bool = False):
    """Single bookmark row in list view."""
    domain = urlparse(bookmark.url).netloc if bookmark.url else ""

    tag_elements = [tag_chip(t) for t in tags[:5]]
    if len(tags) > 5:
        tag_elements.append(Span(f"+{len(tags) - 5}", cls="badge badge-sm"))

    # If no title, use URL (with scheme stripped for mobile via CSS/JS)
    if bookmark.title:
        display_title = bookmark.title
        is_url_as_title = False
    else:
        display_title = bookmark.url
        is_url_as_title = True

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
                    Span(strip_url_scheme(bookmark.url), cls="url-stripped hidden") if is_url_as_title else None,
                    href=bookmark.url,
                    target="_blank",
                    cls="link link-primary font-medium break-all",
                    title=bookmark.url,
                ),
                Button(
                    "\U0001F4DD",  # Memo/note icon
                    cls="ml-1 flex-shrink-0 hover:scale-110 transition-transform",
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
                "Edit",
                cls="btn btn-xs btn-ghost",
                hx_get=f"/bookmarks/{bookmark.id}/edit",
                hx_target="#modal-container",
            ),
            cls="w-12 px-1",
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
                Th("", cls="w-12 px-1"),  # Actions column, no header text
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
                "x",
                cls="btn btn-xs btn-ghost p-0 min-h-0 h-4 w-4",
                hx_delete=f"/bookmarks/{bookmark_id}/tags/{tag.id}",
                hx_swap="outerHTML",
            )
        )

    return Span(
        *children,
        cls="badge badge-neutral gap-1",
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
                ['/', 'Focus search / Clear search'],
                ['j / k', 'Navigate down / up'],
                ['n / p', 'Next / Previous page'],
                ['Enter', 'Open selected link'],
                ['o', 'Open in new tab'],
                ['x', 'Toggle checkbox'],
                ['G', 'Go to last row'],
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

        document.addEventListener('keydown', (e) => {
            // Skip if in input/textarea
            if (e.target.matches('input, textarea, select')) return;

            switch(e.key) {
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
                    if (e.shiftKey) selectRow(rows().length - 1);
                    // gg handled by double-tap
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
                case 'Escape':
                    closeModal();
                    document.querySelectorAll('.bookmark-checkbox').forEach(cb => cb.checked = false);
                    updateBulkBar();
                    break;
                case '?':
                    showKeyboardHelp();
                    break;
            }
        });

        // Update bulk bar when checkboxes change
        document.addEventListener('change', (e) => {
            if (e.target.matches('.bookmark-checkbox')) updateBulkBar();
        });
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
