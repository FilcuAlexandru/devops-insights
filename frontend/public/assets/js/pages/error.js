import { html } from "../core/html.js";
import { emptyState } from "../components/ui.js";

export function renderError(error) {
    return emptyState({
        title: error.status === 404 ? "Not found" : "Something went wrong",
        message: error.message,
        action: html`<button type="button" class="button" data-retry>Try again</button>`,
    });
}
