import { api } from "../core/api.js";
import { html } from "../core/html.js";
import { formatDateTime } from "../core/format.js";
import { renderMarkdown } from "../core/markdown.js";
import { badge, sectionHeader } from "./ui.js";
import { showToast } from "./toast.js";

function analysisBody(analysis) {
    return html`
        <div class="markdown">${renderMarkdown(analysis.response)}</div>
        <p class="muted">
            Generated ${formatDateTime(analysis.created_at)} by <code>${analysis.model}</code>
        </p>
    `;
}

function availability(health) {
    if (health.ready) {
        return badge(`${health.model} ready`, "success");
    }

    return html`
        ${badge(health.available ? "model missing" : "Ollama unreachable", "warning")}
        <p class="muted">${health.error}</p>
    `;
}

function panel({ health, analyses, busy, error }) {
    const [latest, ...previous] = analyses;

    return html`
        ${sectionHeader({
            title: "AI analysis",
            description:
                "Generated locally by Ollama from the collected data. " +
                "Numbers are calculated by the application, not by the model.",
            actions: html`
                <button type="button" class="button button--primary" data-analyze
                        ${health.ready && !busy ? "" : "disabled"}>
                    ${busy ? "Analyzing…" : "Generate analysis"}
                </button>
            `,
        })}
        <div class="availability">${availability(health)}</div>
        ${busy &&
        html`<p class="notice" role="status">
            The local model is working. This can take a minute or two on a laptop.
        </p>`}
        ${error && html`<p class="notice notice--danger" role="alert">${error}</p>`}
        ${latest
            ? analysisBody(latest)
            : html`<p class="muted">No analysis has been generated for this repository yet.</p>`}
        ${previous.length > 0 &&
        html`
            <details class="history">
                <summary>${previous.length} earlier analysis(es)</summary>
                ${previous.map(
                    (analysis) => html`<article class="history__item">${analysisBody(analysis)}</article>`,
                )}
            </details>
        `}
    `;
}

/** Load the AI state of a repository. Health failures degrade to an "unreachable" state. */
export async function loadAnalysisState(repositoryId) {
    const [health, analyses] = await Promise.all([
        api.get("/api/ai/health").catch((error) => ({
            available: false,
            model_available: false,
            ready: false,
            model: "unknown",
            error: error.message,
        })),
        api.get(`/api/ai/repositories/${repositoryId}/analyses`),
    ]);

    return { health, analyses, busy: false, error: null };
}

export const renderAnalysisPanel = (state) => panel(state);

/** Wire the "Generate analysis" button; the panel re-renders itself after every change. */
export function mountAnalysisPanel(root, repositoryId, state) {
    const update = (changes) => {
        Object.assign(state, changes);
        root.innerHTML = String(panel(state));
        root.querySelector("[data-analyze]")?.addEventListener("click", analyze);
    };

    async function analyze() {
        update({ busy: true, error: null });

        try {
            const analysis = await api.post(`/api/ai/repositories/${repositoryId}/analyze`);

            update({ busy: false, analyses: [analysis, ...state.analyses] });
            showToast("Analysis generated.", "success");
        } catch (error) {
            update({ busy: false, error: error.message });
        }
    }

    root.querySelector("[data-analyze]")?.addEventListener("click", analyze);
}
