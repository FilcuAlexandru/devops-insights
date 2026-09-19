import { api } from "../core/api.js";
import { html } from "../core/html.js";
import { formatCompact, formatDelta, formatNumber, timeAgo } from "../core/format.js";
import { barChart, destroyCharts, doughnutChart } from "../components/charts.js";
import { bindCollectButtons, collectionStatus } from "../components/collection.js";
import {
    emptyState,
    pageHeader,
    repositoryTable,
    sectionHeader,
    statCard,
} from "../components/ui.js";

const collectButton = html`<button type="button" class="button button--primary" data-collect>
    Collect now
</button>`;

function technologyFilter(technologies, selected) {
    return html`
        <label class="field field--inline">
            <span class="sr-only">Technology</span>
            <select id="technology-filter" aria-label="Filter by technology">
                <option value="">All technologies</option>
                ${technologies.map(
                    (technology) => html`
                        <option
                            value="${technology.slug}"
                            ${technology.slug === selected ? "selected" : ""}
                        >
                            ${technology.name}
                        </option>
                    `,
                )}
            </select>
        </label>
    `;
}

function growthList(entries) {
    if (entries.length === 0) {
        return emptyState({
            title: "No growth data yet",
            message:
                "Rankings appear once repositories have been collected at least twice and " +
                "gained stars in between.",
        });
    }

    return html`
        <ol class="ranking">
            ${entries.map(
                (entry) => html`
                    <li>
                        <a href="#/repositories/${entry.id}">${entry.full_name}</a>
                        <span class="ranking__value">
                            ${formatDelta(entry.stars_gained)} stars
                            ${entry.stars_per_day !== null &&
                            html`<span class="muted">(${entry.stars_per_day}/day)</span>`}
                        </span>
                    </li>
                `,
            )}
        </ol>
    `;
}

function insights(analyses) {
    if (analyses.length === 0) {
        return emptyState({
            title: "No AI analyses yet",
            message: "Open a repository and use “Generate analysis” to create one.",
        });
    }

    return html`
        <div class="insight-grid">
            ${analyses.map(
                (analysis) => html`
                    <article class="insight">
                        <a href="#/repositories/${analysis.repository_id}">
                            ${analysis.repository_full_name}
                        </a>
                        <p>${analysis.summary}</p>
                        <span class="muted">
                            ${analysis.model} · ${timeAgo(analysis.created_at)}
                        </span>
                    </article>
                `,
            )}
        </div>
    `;
}

function overview(dashboard) {
    const { totals } = dashboard;

    return html`
        <section class="stat-grid" aria-label="Totals">
            ${statCard({ label: "Technologies", value: formatNumber(totals.technologies) })}
            ${statCard({ label: "Repositories", value: formatNumber(totals.repositories) })}
            ${statCard({ label: "Stars", value: formatCompact(totals.stars) })}
            ${statCard({ label: "Forks", value: formatCompact(totals.forks) })}
            ${statCard({ label: "Open issues", value: formatCompact(totals.open_issues) })}
            ${statCard({ label: "Snapshots", value: formatNumber(totals.snapshots) })}
        </section>

        <section class="grid grid--2">
            <article class="card">
                ${sectionHeader({
                    title: "Stars by technology",
                    description: "Total GitHub stars of the tracked repositories.",
                })}
                <div class="chart"><canvas id="technology-chart"></canvas></div>
            </article>
            <article class="card">
                ${sectionHeader({
                    title: "Primary languages",
                    description: "Repositories grouped by their main language.",
                })}
                <div class="chart chart--tall"><canvas id="language-chart"></canvas></div>
            </article>
        </section>

        <section class="grid grid--2-1">
            <article class="card">
                ${sectionHeader({
                    title: "Top repositories",
                    description: "Ordered by stars.",
                })}
                ${repositoryTable(dashboard.top_repositories, { compact: true })}
            </article>
            <article class="card">
                ${sectionHeader({
                    title: "Fastest growing",
                    description: "Stars gained across the collected history.",
                })}
                ${growthList(dashboard.fastest_growing)}
            </article>
        </section>

        <section class="card">
            ${sectionHeader({
                title: "Latest AI insights",
                description: "Summaries of the most recent analyses generated by the local model.",
            })}
            ${insights(dashboard.recent_analyses)}
        </section>
    `;
}

export async function render({ query }) {
    const selected = query.technology ?? "";
    const [dashboard, technologies] = await Promise.all([
        api.get("/api/dashboard", { technology: selected }),
        api.get("/api/technologies"),
    ]);

    const isEmpty = dashboard.totals.repositories === 0;

    const content = html`
        ${pageHeader({
            eyebrow: "Overview",
            title: "Dashboard",
            description: "What is happening across the DevOps ecosystem you track.",
            actions: html`${technologyFilter(technologies, selected)}${collectButton}`,
        })}
        ${(dashboard.last_collection || !isEmpty) && collectionStatus(dashboard.last_collection)}
        ${isEmpty
            ? emptyState({
                  title: "No repositories collected yet",
                  message:
                      "The collector runs automatically, or you can start it now. " +
                      "It takes about a minute.",
                  action: collectButton,
              })
            : overview(dashboard)}
    `;

    return {
        title: "Dashboard",
        content,
        mount(root) {
            root.querySelector("#technology-filter").addEventListener("change", (event) => {
                window.location.hash = event.target.value
                    ? `#/?technology=${encodeURIComponent(event.target.value)}`
                    : "#/";
            });
            bindCollectButtons(root);

            if (!isEmpty) {
                const technologyChart = root.querySelector("#technology-chart");

                // One row per technology, so every label stays readable.
                technologyChart.parentElement.style.height = `${
                    Math.max(280, dashboard.technologies.length * 26 + 40)
                }px`;

                barChart(technologyChart, {
                    labels: dashboard.technologies.map((item) => item.name),
                    values: dashboard.technologies.map((item) => item.stars),
                    label: "Stars",
                    horizontal: true,
                });
                doughnutChart(root.querySelector("#language-chart"), {
                    labels: dashboard.languages.map((item) => item.language),
                    values: dashboard.languages.map((item) => item.repository_count),
                });
            }

            return destroyCharts;
        },
    };
}
