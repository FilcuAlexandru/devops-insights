import { api } from "../core/api.js";
import { html } from "../core/html.js";
import { formatCompact, formatNumber } from "../core/format.js";
import {
    badge,
    emptyState,
    externalLink,
    pageHeader,
    repositoryTable,
    sectionHeader,
    statCard,
} from "../components/ui.js";

export async function render({ params }) {
    const technology = await api.get(`/api/technologies/${encodeURIComponent(params.slug)}`);

    const content = html`
        <nav class="breadcrumb"><a href="#/technologies">Technologies</a></nav>
        ${pageHeader({
            eyebrow: badge(technology.category),
            title: technology.name,
            description: technology.description,
            actions:
                technology.website_url &&
                externalLink(technology.website_url, "Official website ↗", "button"),
        })}
        <section class="stat-grid stat-grid--compact">
            ${statCard({ label: "Repositories", value: formatNumber(technology.repository_count) })}
            ${statCard({ label: "Stars", value: formatCompact(technology.total_stars) })}
        </section>
        <section class="card">
            ${sectionHeader({
                title: "Repositories",
                description: `Tracked repositories for ${technology.name}.`,
            })}
            ${technology.repositories.length > 0
                ? repositoryTable(technology.repositories, { showTechnology: false })
                : emptyState({
                      title: "No repositories collected yet",
                      message: "Run a collection from the dashboard to fetch them.",
                  })}
        </section>
    `;

    return { title: technology.name, content };
}
