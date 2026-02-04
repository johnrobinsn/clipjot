package com.clipjot.android;

import android.app.Application;
import android.content.Intent;
import android.graphics.drawable.Icon;
import android.os.Build;

import androidx.annotation.RequiresApi;
import androidx.core.content.pm.ShortcutInfoCompat;
import androidx.core.content.pm.ShortcutManagerCompat;
import androidx.core.graphics.drawable.IconCompat;

import com.clipjot.android.ui.share.ShareActivity;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/**
 * Application class for ClipJot Android client.
 */
public class ClipJotApplication extends Application {

    private static final String SHARE_SHORTCUT_ID = "share_shortcut";

    @Override
    public void onCreate() {
        super.onCreate();

        // Register the sharing shortcut for Direct Share
        registerShareShortcut();
    }

    /**
     * Registers a dynamic shortcut for Direct Share support.
     * This makes ClipJot appear in the direct share targets list
     * (the top row of the share sheet) instead of being buried under "More...".
     */
    private void registerShareShortcut() {
        Set<String> categories = new HashSet<>();
        categories.add("com.clipjot.android.category.SHARE_TARGET");

        ShortcutInfoCompat shortcut = new ShortcutInfoCompat.Builder(this, SHARE_SHORTCUT_ID)
                .setShortLabel(getString(R.string.share_shortcut_short_label))
                .setLongLabel(getString(R.string.share_shortcut_long_label))
                .setIcon(IconCompat.createWithResource(this, R.mipmap.ic_launcher))
                .setIntent(new Intent(Intent.ACTION_SEND)
                        .setClass(this, ShareActivity.class)
                        .setType("text/plain"))
                .setCategories(categories)
                .setLongLived(true)
                .build();

        ShortcutManagerCompat.pushDynamicShortcut(this, shortcut);
    }
}
