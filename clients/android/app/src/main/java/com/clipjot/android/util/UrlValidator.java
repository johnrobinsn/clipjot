package com.clipjot.android.util;

import android.util.Patterns;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Utility class for URL extraction and validation.
 */
public class UrlValidator {

    private static final Pattern URL_PATTERN = Pattern.compile(
            "https?://[\\w\\-._~:/?#\\[\\]@!$&'()*+,;=%]+"
    );

    /**
     * Extract a URL from text that may contain other content.
     */
    public static String extractUrl(String text) {
        if (text == null || text.isEmpty()) {
            return null;
        }

        // Try to match a URL pattern
        Matcher matcher = URL_PATTERN.matcher(text);
        if (matcher.find()) {
            return matcher.group();
        }

        // Check if the entire text is a URL
        String trimmed = text.trim();
        if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
            return trimmed;
        }

        return null;
    }

    /**
     * Extract a title from text that contains more than just a URL.
     */
    public static String extractTitle(String text, String url) {
        if (text == null || url == null) {
            return null;
        }

        // Remove the URL from the text
        String remaining = text.replace(url, "").trim();

        // Clean up any remaining punctuation or whitespace
        remaining = remaining.replaceAll("^[\\s\\-:]+", "").replaceAll("[\\s\\-:]+$", "");

        if (!remaining.isEmpty()) {
            return remaining;
        }
        return null;
    }

    /**
     * Check if a string is a valid URL.
     */
    public static boolean isValidUrl(String url) {
        if (url == null || url.isEmpty()) {
            return false;
        }
        // Accept localhost URLs for development
        if (url.matches("^https?://localhost(:\\d+)?(/.*)?$")) {
            return true;
        }
        // Accept IP address URLs (including 10.0.2.2 for Android emulator)
        if (url.matches("^https?://\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}(:\\d+)?(/.*)?$")) {
            return true;
        }
        return Patterns.WEB_URL.matcher(url).matches();
    }

    /**
     * Normalize a backend URL (add https if missing, remove trailing slash).
     */
    public static String normalizeBackendUrl(String url) {
        if (url == null || url.isEmpty()) {
            return null;
        }

        String normalized = url.trim();

        // Add protocol if missing
        if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
            normalized = "https://" + normalized;
        }

        // Remove trailing slashes
        normalized = normalized.replaceAll("/+$", "");

        return normalized;
    }
}
