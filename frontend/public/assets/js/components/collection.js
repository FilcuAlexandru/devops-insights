import { app } from "../core/app.js";
import { api } from "../core/api.js";
import { html } from "../core/html.js";
import { formatDateTime, timeAgo } from "../core/format.js";
import { badge } from "./ui.js";
import { showToast } from "./toast.js";

const POLL_INTERVAL_MILLISECONDS = 3000;
const POLL_LIMIT = 200;

const STATUS_TONES = {
    running: "info",
    succeeded: "success",
    partial: "warning",
    failed: "danger",
};

/** One-line summary of the most recent collection run, with failures listed underneath. */
export function collectionStatus(run) {
    if (!run) {
        return html`
            <div class="notice">
                <strong>No data collected yet.</strong>
                <span>Use “Collect now” to fetch the tracked repositories from GitHub.</span>
            </div>
        `;
    }

    const finished = run.finished_at ? timeAgo(run.finished_at) : "in progress";

    return html`
        <div class="notice notice--${STATUS_TONES[run.status] ?? "info"}">
            <div class="notice__row">
                ${badge(run.status, STATUS_TONES[run.status] ?? "neutral")}
                <span>
                    Last collection (${run.trigger}): ${run.succeeded} of ${run.total} repositories,
                    ${finished}
                </span>
                <span class="muted">started ${formatDateTime(run.started_at)}</span>
            </div>
            ${run.errors.length > 0 &&
            html`
                <details>
                    <summary>${run.errors.length} problem(s)</summary>
                    <ul class="error-list">
                        ${run.errors.map(
                            (error) =>
                                html`<li><code>${error.repository}</code> ${error.error}</li>`,
                        )}
                    </ul>
                </details>
            `}
        </div>
    `;
}

async function waitForRunToFinish() {
    for (let attempt = 0; attempt < POLL_LIMIT; attempt += 1) {
        const [latest] = await api.get("/api/collection/runs", { limit: 1 });

        if (latest && latest.status !== "running") {
            return latest;
        }

        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MILLISECONDS));
    }

    throw new Error("The collection is taking longer than expected. Check back later.");
}

function announce(run) {
    if (run.status === "succeeded") {
        showToast(`Collected ${run.succeeded} repositories.`, "success");
    } else if (run.status === "partial") {
        showToast(
            `Collected ${run.succeeded} of ${run.total}. First problem: ${run.errors[0]?.error}`,
            "error",
        );
    } else {
        showToast(`Collection failed: ${run.errors[0]?.error ?? "unknown error"}`, "error");
    }
}

/** Make every `[data-collect]` button under `root` start a collection and refresh the page. */
export function bindCollectButtons(root) {
    root.querySelectorAll("[data-collect]").forEach((button) => {
        button.addEventListener("click", async () => {
            const label = button.textContent;
            button.disabled = true;
            button.textContent = "Collecting…";

            try {
                try {
                    await api.post("/api/collection/run");
                    showToast("Collection started. This takes about a minute.", "info");
                } catch (error) {
                    if (error.status !== 409) {
                        throw error;
                    }

                    showToast("A collection is already running. Waiting for it.", "info");
                }

                announce(await waitForRunToFinish());
                app.refresh();
            } catch (error) {
                showToast(error.message, "error");
                button.disabled = false;
                button.textContent = label;
            }
        });
    });
}
