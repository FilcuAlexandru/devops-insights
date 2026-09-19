import { escapeHtml } from "../core/html.js";

const DISPLAY_MILLISECONDS = 6000;

/** Show a short notification. `tone` is "info", "success" or "error". */
export function showToast(message, tone = "info") {
    const container = document.getElementById("toasts");

    if (!container) {
        return;
    }

    const toast = document.createElement("div");
    toast.className = `toast toast--${tone}`;
    toast.innerHTML = escapeHtml(message);
    container.append(toast);

    setTimeout(() => toast.remove(), DISPLAY_MILLISECONDS);
}
