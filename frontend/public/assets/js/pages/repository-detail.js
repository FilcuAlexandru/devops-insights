import { api } from "../core/api.js";
import { html } from "../core/html.js";
import { formatDate, formatDateTime, formatDelta, formatNumber, timeAgo } from "../core/format.js";
import {
    loadAnalysisState,
    mountAnalysisPanel,
    renderAnalysisPanel,
} from "../components/analysis-panel.js";
import { destroyCharts, lineChart } from "../components/charts.js";
import {
    badge,
    emptyState,
    externalLink,
    pageHeader,
    sectionHeader,
    statCard,
} from "../components/ui.js";

const SNAPSHOT_TABLE_LIMIT = 20;

const CHARTS = [
    { id: "stars", title: "Stars", key: "stars" },
    { id: "forks", title: "Forks", key: "forks" },
    { id: "issues", title: "Open issues", key: "open_issues" },
];

function changeHint(change) {
    if (change === null) {
        return "";
    }

    return change === 0 ? "no change" : `${formatDelta(change)} since first snapshot`;
}

function metricCard(label, value, change) {
    return statCard({ label, value: formatNumber(value), hint: changeHint(change) });
}

function trendSection(snapshots, trend) {
    if (snapshots.length < 2) {
        return emptyState({
            title: "Not enough history yet",
            message:
                "Trends need at least two collections. Run “Collect now” again later, " +
                "or wait for the scheduled collector.",
        });
    }

    return html`
        <p class="muted">
            ${trend.snapshot_count} snapshots between ${formatDateTime(trend.first_collected_at)}
            and ${formatDateTime(trend.last_collected_at)}.
            ${trend.stars_per_day !== null && `Average growth: ${trend.stars_per_day} stars per day.`}
        </p>
        <div class="grid grid--3">
            ${CHARTS.map(
                (chart) => html`
                    <figure class="chart-figure">
                        <figcaption>${chart.title}</figcaption>
                        <div class="chart"><canvas id="chart-${chart.id}"></canvas></div>
                    </figure>
                `,
            )}
        </div>
    `;
}

function snapshotTable(snapshots) {
    const latest = [...snapshots].reverse().slice(0, SNAPSHOT_TABLE_LIMIT);

    return html`
        <div class="table-wrap">
            <table class="table">
                <thead>
                    <tr>
                        <th>Collected</th>
                        <th class="num">Stars</th>
                        <th class="num">Forks</th>
                        <th class="num">Open issues</th>
                    </tr>
                </thead>
                <tbody>
                    ${latest.map(
                        (snapshot) => html`
                            <tr>
                                <td>${formatDateTime(snapshot.collected_at)}</td>
                                <td class="num">${formatNumber(snapshot.stars)}</td>
                                <td class="num">${formatNumber(snapshot.forks)}</td>
                                <td class="num">${formatNumber(snapshot.open_issues)}</td>
                            </tr>
                        `,
                    )}
                </tbody>
            </table>
        </div>
        ${snapshots.length > SNAPSHOT_TABLE_LIMIT &&
        html`<p class="muted">Showing the latest ${SNAPSHOT_TABLE_LIMIT} of ${snapshots.length}.</p>`}
    `;
}

function details(repository) {
    const rows = [
        ["Default branch", html`<code>${repository.default_branch}</code>`],
        ["License", repository.license_name ?? "None declared"],
        ["Created on GitHub", formatDate(repository.created_at)],
        ["Last push", `${formatDate(repository.pushed_at)} (${timeAgo(repository.pushed_at)})`],
        ["Last collected", `${formatDateTime(repository.last_collected_at)}`],
    ];

    return html`
        <dl class="details">
            ${rows.map(([term, value]) => html`<div><dt>${term}</dt><dd>${value}</dd></div>`)}
        </dl>
    `;
}

export async function render({ params }) {
    const id = encodeURIComponent(params.id);
    const [repository, snapshots, trend, aiState] = await Promise.all([
        api.get(`/api/repositories/${id}`),
        api.get(`/api/repositories/${id}/snapshots`),
        api.get(`/api/repositories/${id}/trend`),
        loadAnalysisState(id),
    ]);

    const hasHistory = snapshots.length >= 2;
    const change = hasHistory ? trend.change : null;

    const content = html`
        <nav class="breadcrumb">
            <a href="#/repositories">Repositories</a> /
            <a href="#/technologies/${repository.technology_slug}">${repository.technology_name}</a>
        </nav>
        ${pageHeader({
            eyebrow: html`${badge(repository.technology_name)}
            ${repository.primary_language && badge(repository.primary_language)}
            ${repository.archived && badge("archived", "warning")}`,
            title: repository.full_name,
            description: repository.description,
            actions: externalLink(repository.url, "View on GitHub ↗", "button button--primary"),
        })}

        <section class="stat-grid stat-grid--compact" aria-label="Current metrics">
            ${metricCard("Stars", repository.stars, change?.stars ?? null)}
            ${metricCard("Forks", repository.forks, change?.forks ?? null)}
            ${metricCard("Open issues", repository.open_issues, change?.open_issues ?? null)}
        </section>

        <section class="card">
            ${sectionHeader({
                title: "Trends",
                description: "How this repository changed across the collected snapshots.",
            })}
            ${trendSection(snapshots, trend)}
        </section>

        <section class="card" id="ai-panel">${renderAnalysisPanel(aiState)}</section>

        <section class="grid grid--2">
            <article class="card">
                ${sectionHeader({ title: "Details" })} ${details(repository)}
            </article>
            <article class="card">
                ${sectionHeader({ title: "Snapshots", description: "Collected statistics." })}
                ${snapshots.length > 0
                    ? snapshotTable(snapshots)
                    : emptyState({
                          title: "No snapshots yet",
                          message: "Snapshots are created by every collection run.",
                      })}
            </article>
        </section>
    `;

    return {
        title: repository.full_name,
        content,
        mount(root) {
            mountAnalysisPanel(root.querySelector("#ai-panel"), id, aiState);

            if (hasHistory) {
                const labels = snapshots.map((snapshot) => formatDateTime(snapshot.collected_at));

                CHARTS.forEach((chart, index) =>
                    lineChart(root.querySelector(`#chart-${chart.id}`), {
                        labels,
                        values: snapshots.map((snapshot) => snapshot[chart.key]),
                        label: chart.title,
                        seriesIndex: index,
                    }),
                );
            }

            return destroyCharts;
        },
    };
}
