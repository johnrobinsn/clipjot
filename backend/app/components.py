"""Reusable FastHTML/FT components for LinkJot UI.

These components provide consistent styling using DaisyUI classes.
"""

from fasthtml.common import *
from typing import Optional
from urllib.parse import urlparse

from .models import Bookmark, Tag, User


# =============================================================================
# Page Layout Components
# =============================================================================

def page_head(title: str = "LinkJot"):
    """Generate page head with CSS/JS dependencies."""
    return (
        Title(title),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
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
    )


def page_layout(content, title: str = "LinkJot", user: Optional[User] = None, flash: Optional[str] = None):
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
        Input(
            type="search",
            name="q",
            placeholder="Search bookmarks...",
            cls="input input-bordered w-48 md:w-64",
            id="search-input",
        ),
        cls="form-control" if user else "hidden",
        action="/",
        method="get",
    )

    return Nav(
        Div(
            A("LinkJot", href="/", cls="btn btn-ghost text-xl"),
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
        Li(A("My Bookmarks", href="/")),
        Li(A("Settings", href="/settings")),
        Li(A("Tags", href="/settings/tags")),
        Li(A("API Tokens", href="/settings/tokens")),
        Li(A("Sessions", href="/settings/sessions")),
        Li(A("Export", href="/export")),
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

def bookmark_row(bookmark: Bookmark, tags: list[Tag], selected: bool = False):
    """Single bookmark row in list view."""
    domain = urlparse(bookmark.url).netloc if bookmark.url else ""

    tag_elements = [tag_chip(t) for t in tags[:5]]
    if len(tags) > 5:
        tag_elements.append(Span(f"+{len(tags) - 5}", cls="badge badge-sm"))

    return Tr(
        # Checkbox
        Td(
            Input(
                type="checkbox",
                cls="checkbox checkbox-sm bookmark-checkbox",
                name="selected",
                value=str(bookmark.id),
                checked=selected,
            )
        ),
        # Title & URL
        Td(
            A(
                bookmark.title or bookmark.url,
                href=bookmark.url,
                target="_blank",
                cls="link link-primary font-medium truncate block",
                title=bookmark.url,
            ),
            Span(domain, cls="text-xs text-base-content/60"),
            cls="max-w-md",
        ),
        # Tags
        Td(
            Div(*tag_elements, cls="flex flex-wrap gap-1"),
        ),
        # Date
        Td(
            Span(
                format_date(bookmark.created_at),
                cls="text-sm text-base-content/70",
                title=bookmark.created_at,
            )
        ),
        # Actions
        Td(
            Div(
                Button(
                    "Edit",
                    cls="btn btn-xs btn-ghost",
                    hx_get=f"/bookmarks/{bookmark.id}/edit",
                    hx_target="#modal-container",
                ),
                Button(
                    "Delete",
                    cls="btn btn-xs btn-ghost text-error",
                    hx_delete=f"/bookmarks/{bookmark.id}",
                    hx_confirm="Delete this bookmark?",
                    hx_target=f"#bookmark-{bookmark.id}",
                    hx_swap="outerHTML",
                ),
                cls="flex gap-1",
            ),
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
                    )
                ),
                Th("Bookmark"),
                Th("Tags"),
                Th("Added"),
                Th("Actions"),
            )
        ),
        Tbody(*rows, id="bookmark-list"),
        cls="table table-zebra w-full",
    )


def bookmark_form(bookmark: Optional[Bookmark] = None, tags: list[Tag] = None, all_tags: list[Tag] = None):
    """Form for adding/editing a bookmark."""
    is_edit = bookmark is not None
    action = f"/bookmarks/{bookmark.id}" if is_edit else "/bookmarks/add"
    tag_ids = {t.id for t in (tags or [])}

    tag_checkboxes = [
        Label(
            Input(
                type="checkbox",
                name="tags",
                value=str(t.id),
                checked=t.id in tag_ids,
                cls="checkbox checkbox-sm",
            ),
            tag_chip(t),
            cls="cursor-pointer flex items-center gap-1",
        )
        for t in (all_tags or [])
    ]

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
        # Tags
        Div(
            Label("Tags", cls="label"),
            Div(*tag_checkboxes, cls="flex flex-wrap gap-2"),
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
                "Save" if is_edit else "Add Bookmark",
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
    """Display a tag as a colored chip."""
    # Determine text color based on background brightness
    bg_color = tag.color or "#6b7280"

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
        cls="badge gap-1",
        style=f"background-color: {bg_color}; color: white;",
    )


def tag_list_item(tag: dict):
    """Tag item in settings list (with count)."""
    return Tr(
        Td(
            Div(
                Span(cls="w-4 h-4 rounded", style=f"background-color: {tag['color']};"),
                Span(tag["name"], cls="font-medium"),
                cls="flex items-center gap-2",
            )
        ),
        Td(Span(f"{tag['bookmark_count']} bookmarks", cls="text-sm text-base-content/70")),
        Td(
            Div(
                Button(
                    "Edit",
                    cls="btn btn-xs btn-ghost",
                    hx_get=f"/settings/tags/{tag['id']}/edit",
                    hx_target="#modal-container",
                ),
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
        children.append(A("Prev", href=f"{base_url}?page={page-1}", cls="btn btn-sm"))
    children.extend([page_link(p) for p in pages])
    if page < total_pages:
        children.append(A("Next", href=f"{base_url}?page={page+1}", cls="btn btn-sm"))

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
            hx_confirm="Delete selected bookmarks?",
        ),
        Button(
            "Add Tag",
            cls="btn btn-sm btn-ghost mr-2",
            hx_get="/bookmarks/bulk/add-tag",
            hx_target="#modal-container",
        ),
        Button(
            "Remove Tag",
            cls="btn btn-sm btn-ghost",
            hx_get="/bookmarks/bulk/remove-tag",
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
        let currentIndex = -1;
        const rows = () => document.querySelectorAll('#bookmark-list tr');

        function selectRow(index) {
            const r = rows();
            if (currentIndex >= 0 && currentIndex < r.length) {
                r[currentIndex].classList.remove('bg-base-300');
            }
            currentIndex = Math.max(0, Math.min(index, r.length - 1));
            if (currentIndex >= 0 && currentIndex < r.length) {
                r[currentIndex].classList.add('bg-base-300');
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

        document.addEventListener('keydown', (e) => {
            // Skip if in input/textarea
            if (e.target.matches('input, textarea, select')) return;

            switch(e.key) {
                case '/':
                    e.preventDefault();
                    document.getElementById('search-input')?.focus();
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
                case 'G':
                    selectRow(rows().length - 1);
                    break;
                case 'Escape':
                    closeModal();
                    document.querySelectorAll('.bookmark-checkbox').forEach(cb => cb.checked = false);
                    updateBulkBar();
                    break;
                case '?':
                    // Show help modal
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
