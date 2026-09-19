import { html } from "../core/html.js";
import { emptyState } from "../components/ui.js";

export async function render() {
    return {
        title: "Not found",
        content: emptyState({
            title: "Page not found",
            message: "The page you are looking for does not exist.",
            action: html`<a class="button button--primary" href="#/">Back to the dashboard</a>`,
        }),
    };
}
