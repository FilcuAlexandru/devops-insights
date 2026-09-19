import { api } from "../core/api.js";
import { html } from "../core/html.js";
import { emptyState, pageHeader, repositoryTable } from "../components/ui.js";

const SEARCH_DEBOUNCE_MILLISECONDS = 250;

const SORT_OPTIONS = [
    ["stars", "Stars"],
    ["forks", "Forks"],
    ["issues", "Open issues"],
    ["activity", "Last push"],
    ["name", "Name"],
];

function results(repositories) {
    if (repositories.length === 0) {
        return emptyState({
            title: "No repositories match",
            message: "Try a different search or clear the filters.",
        });
    }

    return html`
        <p class="muted" aria-live="polite">${repositories.length} repositories</p>
        ${repositoryTable(repositories)}
    `;
}

function option(value, label, selected) {
    return html`<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`;
}

export async function render({ query }) {
    const technologies = await api.get("/api/technologies");
    const state = {
        search: query.search ?? "",
        technology: query.technology ?? "",
        sort: query.sort ?? "stars",
        order: query.order ?? "desc",
    };
    const repositories = await api.get("/api/repositories", state);

    const content = html`
        ${pageHeader({
            eyebrow: "Source code",
            title: "Repositories",
            description: "Every repository tracked by the platform.",
        })}
        <form class="toolbar card" id="filters" role="search">
            <label class="field">
                <span>Search</span>
                <input type="search" name="search" value="${state.search}"
                       placeholder="Name or description" autocomplete="off">
            </label>
            <label class="field">
                <span>Technology</span>
                <select name="technology">
                    ${option("", "All technologies", state.technology)}
                    ${technologies.map((item) => option(item.slug, item.name, state.technology))}
                </select>
            </label>
            <label class="field">
                <span>Sort by</span>
                <select name="sort">
                    ${SORT_OPTIONS.map(([value, label]) => option(value, label, state.sort))}
                </select>
            </label>
            <label class="field">
                <span>Order</span>
                <select name="order">
                    ${option("desc", "Highest first", state.order)}
                    ${option("asc", "Lowest first", state.order)}
                </select>
            </label>
        </form>
        <section class="card" id="results">${results(repositories)}</section>
    `;

    return {
        title: "Repositories",
        content,
        mount(root) {
            const form = root.querySelector("#filters");
            const target = root.querySelector("#results");
            let timer;

            async function reload() {
                const values = Object.fromEntries(new FormData(form));

                history.replaceState(null, "", `#/repositories?${new URLSearchParams(values)}`);

                try {
                    target.innerHTML = String(results(await api.get("/api/repositories", values)));
                } catch (error) {
                    target.innerHTML = String(
                        emptyState({ title: "Could not load repositories", message: error.message }),
                    );
                }
            }

            form.addEventListener("submit", (event) => event.preventDefault());
            form.addEventListener("change", reload);
            form.addEventListener("input", (event) => {
                if (event.target.name === "search") {
                    clearTimeout(timer);
                    timer = setTimeout(reload, SEARCH_DEBOUNCE_MILLISECONDS);
                }
            });

            return () => clearTimeout(timer);
        },
    };
}
