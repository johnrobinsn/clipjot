package com.clipjot.android.ui.links;

import android.content.res.Configuration;
import android.net.Uri;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.HorizontalScrollView;
import android.widget.ImageButton;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.RecyclerView;

import com.clipjot.android.R;
import com.clipjot.android.data.api.model.BookmarkResponse;
import com.clipjot.android.data.api.model.Tag;
import com.google.android.material.card.MaterialCardView;
import com.google.android.material.checkbox.MaterialCheckBox;
import com.google.android.material.chip.Chip;
import com.google.android.material.chip.ChipGroup;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * RecyclerView adapter for displaying bookmarks.
 */
public class BookmarkAdapter extends RecyclerView.Adapter<BookmarkAdapter.ViewHolder> {

    private List<BookmarkResponse> bookmarks = new ArrayList<>();
    private final Set<Integer> selectedIds = new HashSet<>();
    private boolean selectionMode = false;
    private OnBookmarkClickListener listener;

    public interface OnBookmarkClickListener {
        void onBookmarkClick(BookmarkResponse bookmark);
        void onEditClick(BookmarkResponse bookmark);
        void onSelectionChanged(Set<Integer> selectedIds);
        void onLongClick(BookmarkResponse bookmark);
    }

    public void setOnBookmarkClickListener(OnBookmarkClickListener listener) {
        this.listener = listener;
    }

    public void setBookmarks(List<BookmarkResponse> newBookmarks) {
        this.bookmarks = new ArrayList<>(newBookmarks);
        notifyDataSetChanged();
    }

    /**
     * Updates bookmarks using DiffUtil for smooth animations without flashing.
     */
    public void updateBookmarks(List<BookmarkResponse> newBookmarks) {
        List<BookmarkResponse> oldBookmarks = this.bookmarks;
        List<BookmarkResponse> newList = new ArrayList<>(newBookmarks);

        DiffUtil.DiffResult diffResult = DiffUtil.calculateDiff(new DiffUtil.Callback() {
            @Override
            public int getOldListSize() {
                return oldBookmarks.size();
            }

            @Override
            public int getNewListSize() {
                return newList.size();
            }

            @Override
            public boolean areItemsTheSame(int oldPos, int newPos) {
                return oldBookmarks.get(oldPos).getId() == newList.get(newPos).getId();
            }

            @Override
            public boolean areContentsTheSame(int oldPos, int newPos) {
                BookmarkResponse oldItem = oldBookmarks.get(oldPos);
                BookmarkResponse newItem = newList.get(newPos);
                // Compare relevant fields
                return oldItem.getId() == newItem.getId()
                        && equals(oldItem.getTitle(), newItem.getTitle())
                        && equals(oldItem.getUrl(), newItem.getUrl())
                        && equals(oldItem.getComment(), newItem.getComment())
                        && tagsEqual(oldItem.getTags(), newItem.getTags());
            }

            private boolean equals(String a, String b) {
                return (a == null && b == null) || (a != null && a.equals(b));
            }

            private boolean tagsEqual(List<Tag> a, List<Tag> b) {
                if (a == null && b == null) return true;
                if (a == null || b == null) return false;
                if (a.size() != b.size()) return false;
                for (int i = 0; i < a.size(); i++) {
                    if (a.get(i).getId() != b.get(i).getId()) return false;
                }
                return true;
            }
        });

        this.bookmarks = newList;
        diffResult.dispatchUpdatesTo(this);
    }

    public void addBookmarks(List<BookmarkResponse> newBookmarks) {
        int startPos = bookmarks.size();
        bookmarks.addAll(newBookmarks);
        notifyItemRangeInserted(startPos, newBookmarks.size());
    }

    public void updateBookmark(BookmarkResponse updated) {
        for (int i = 0; i < bookmarks.size(); i++) {
            if (bookmarks.get(i).getId() == updated.getId()) {
                bookmarks.set(i, updated);
                notifyItemChanged(i);
                break;
            }
        }
    }

    public void removeBookmark(int bookmarkId) {
        for (int i = 0; i < bookmarks.size(); i++) {
            if (bookmarks.get(i).getId() == bookmarkId) {
                bookmarks.remove(i);
                selectedIds.remove(bookmarkId);
                notifyItemRemoved(i);
                break;
            }
        }
    }

    public void removeBookmarks(Set<Integer> ids) {
        for (int i = bookmarks.size() - 1; i >= 0; i--) {
            if (ids.contains(bookmarks.get(i).getId())) {
                bookmarks.remove(i);
                notifyItemRemoved(i);
            }
        }
        selectedIds.removeAll(ids);
    }

    public boolean isSelectionMode() {
        return selectionMode;
    }

    public void setSelectionMode(boolean selectionMode) {
        if (this.selectionMode != selectionMode) {
            this.selectionMode = selectionMode;
            if (!selectionMode) {
                selectedIds.clear();
            }
            notifyDataSetChanged();
        }
    }

    public Set<Integer> getSelectedIds() {
        return new HashSet<>(selectedIds);
    }

    public void clearSelection() {
        selectedIds.clear();
        setSelectionMode(false);
    }

    public void selectAll() {
        selectedIds.clear();
        for (BookmarkResponse bookmark : bookmarks) {
            selectedIds.add(bookmark.getId());
        }
        notifyDataSetChanged();
        if (listener != null) {
            listener.onSelectionChanged(new HashSet<>(selectedIds));
        }
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_bookmark, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        BookmarkResponse bookmark = bookmarks.get(position);
        holder.bind(bookmark);
    }

    @Override
    public int getItemCount() {
        return bookmarks.size();
    }

    class ViewHolder extends RecyclerView.ViewHolder {
        private final MaterialCardView card;
        private final MaterialCheckBox checkbox;
        private final TextView titleText;
        private final TextView domainText;
        private final HorizontalScrollView tagsScrollView;
        private final ChipGroup tagsChipGroup;
        private final TextView commentIndicator;
        private final ImageButton editButton;

        ViewHolder(View itemView) {
            super(itemView);
            card = itemView.findViewById(R.id.bookmarkCard);
            checkbox = itemView.findViewById(R.id.selectionCheckbox);
            titleText = itemView.findViewById(R.id.titleText);
            domainText = itemView.findViewById(R.id.domainText);
            tagsScrollView = itemView.findViewById(R.id.tagsScrollView);
            tagsChipGroup = itemView.findViewById(R.id.tagsChipGroup);
            commentIndicator = itemView.findViewById(R.id.commentIndicator);
            editButton = itemView.findViewById(R.id.editButton);
        }

        void bind(BookmarkResponse bookmark) {
            // Title - strip URL scheme in portrait mode when showing URL as title
            String title = bookmark.getTitle();
            if (title == null || title.isEmpty()) {
                String url = bookmark.getUrl();
                if (isPortrait() && url != null) {
                    title = stripUrlScheme(url);
                } else {
                    title = url;
                }
            }
            titleText.setText(title);

            // Domain
            String domain = extractDomain(bookmark.getUrl());
            domainText.setText(domain);

            // Tags
            List<Tag> tags = bookmark.getTags();
            if (tags != null && !tags.isEmpty()) {
                tagsScrollView.setVisibility(View.VISIBLE);
                tagsChipGroup.removeAllViews();
                for (Tag tag : tags) {
                    Chip chip = new Chip(itemView.getContext());
                    chip.setText(tag.getName());
                    chip.setTextSize(11);
                    chip.setChipMinHeight(itemView.getResources().getDimensionPixelSize(R.dimen.chip_min_height_small));
                    chip.setClickable(false);
                    tagsChipGroup.addView(chip);
                }
            } else {
                tagsScrollView.setVisibility(View.GONE);
            }

            // Comment indicator
            String comment = bookmark.getComment();
            if (comment != null && !comment.isEmpty()) {
                commentIndicator.setVisibility(View.VISIBLE);
                // Truncate long comments
                String displayComment = comment.length() > 50 ? comment.substring(0, 50) + "…" : comment;
                commentIndicator.setText(displayComment);
            } else {
                commentIndicator.setVisibility(View.GONE);
            }

            // Selection mode
            checkbox.setVisibility(selectionMode ? View.VISIBLE : View.GONE);
            editButton.setVisibility(selectionMode ? View.GONE : View.VISIBLE);

            if (selectionMode) {
                boolean isSelected = selectedIds.contains(bookmark.getId());
                checkbox.setChecked(isSelected);
                card.setChecked(isSelected);
            } else {
                card.setChecked(false);
            }

            // Click listeners
            card.setOnClickListener(v -> {
                if (selectionMode) {
                    toggleSelection(bookmark);
                } else if (listener != null) {
                    listener.onBookmarkClick(bookmark);
                }
            });

            card.setOnLongClickListener(v -> {
                if (!selectionMode && listener != null) {
                    listener.onLongClick(bookmark);
                }
                return true;
            });

            checkbox.setOnClickListener(v -> toggleSelection(bookmark));

            editButton.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onEditClick(bookmark);
                }
            });
        }

        private void toggleSelection(BookmarkResponse bookmark) {
            int id = bookmark.getId();
            if (selectedIds.contains(id)) {
                selectedIds.remove(id);
            } else {
                selectedIds.add(id);
            }
            notifyItemChanged(getAdapterPosition());
            if (listener != null) {
                listener.onSelectionChanged(new HashSet<>(selectedIds));
            }
        }

        private String extractDomain(String url) {
            try {
                Uri uri = Uri.parse(url);
                String host = uri.getHost();
                if (host != null) {
                    // Remove www. prefix
                    if (host.startsWith("www.")) {
                        host = host.substring(4);
                    }
                    return host;
                }
            } catch (Exception ignored) {
            }
            return url;
        }

        private boolean isPortrait() {
            int orientation = itemView.getContext().getResources().getConfiguration().orientation;
            return orientation == Configuration.ORIENTATION_PORTRAIT;
        }

        private String stripUrlScheme(String url) {
            if (url == null) return null;
            if (url.startsWith("https://")) {
                return url.substring(8);
            } else if (url.startsWith("http://")) {
                return url.substring(7);
            }
            return url;
        }
    }
}
