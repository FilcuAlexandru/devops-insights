import { html, safeUrl } from "../core/html.js";
import { formatNumber, timeAgo } from "../core/format.js";

export const pageHeader = ({ eyebrow, title, description, actions }) => html`
    <header class="page-header">
        <div class="page-header__text">
            ${eyebrow && html`<p class="eyebrow">${eyebrow}</p>`}
            <h1>${title}</h1>
            ${description && html`<p class="lead">${description}</p>`}
        </div>
        ${actions && html`<div class="page-header__actions">${actions}</div>`}
    </header>
`;

export const statCard = ({ label, value, hint }) => html`
    <div class="stat">
        <span class="stat__label">${label}</span>
        <strong class="stat__value">${value}</strong>
        ${hint && html`<span class="stat__hint">${hint}</span>`}
    </div>
`;

export const emptyState = ({ title, message, action }) => html`
    <div class="empty">
        <h3>${title}</h3>
        <p>${message}</p>
        ${action}
    </div>
`;

export const badge = (text, tone = "neutral") => html`<span class="badge badge--${tone}">${text}</span>`;

export const sectionHeader = ({ title, description, actions }) => html`
    <div class="section-header">
        <div>
            <h2>${title}</h2>
            ${description && html`<p class="muted">${description}</p>`}
        </div>
        ${actions}
    </div>
`;

export const externalLink = (url, label, className = "") => html`
    <a class="${className}" href="${safeUrl(url)}" target="_blank" rel="noopener noreferrer">
        ${label}
    </a>
`;

/**
 * A table of repositories, used on the dashboard, technology and repositories pages.
 * `compact` drops the technology, description and last push for narrow containers.
 */
export function repositoryTable(repositories, { showTechnology = true, compact = false } = {}) {
    showTechnology &&= !compact;

    return html`
        <div class="table-wrap">
            <table class="table">
                <thead>
                    <tr>
                        <th>Repository</th>
                        ${showTechnology && html`<th>Technology</th>`}
                        <th>Language</th>
                        <th class="num">Stars</th>
                        <th class="num">Forks</th>
                        <th class="num">Issues</th>
                        ${!compact && html`<th>Last push</th>`}
                    </tr>
                </thead>
                <tbody>
                    ${repositories.map(
                        (repository) => html`
                            <tr>
                                <td>
                                    <a class="table__title" href="#/repositories/${repository.id}">
                                        ${repository.full_name}
                                    </a>
                                    ${repository.archived && badge("archived", "warning")}
                                    ${!compact &&
                                    html`<p class="table__subtitle">${repository.description ?? ""}</p>`}
                                </td>
                                ${showTechnology &&
                                html`<td>
                                    <a href="#/technologies/${repository.technology_slug}">
                                        ${repository.technology_name}
                                    </a>
                                </td>`}
                                <td>${repository.primary_language ?? "—"}</td>
                                <td class="num">${formatNumber(repository.stars)}</td>
                                <td class="num">${formatNumber(repository.forks)}</td>
                                <td class="num">${formatNumber(repository.open_issues)}</td>
                                ${!compact && html`<td>${timeAgo(repository.pushed_at)}</td>`}
                            </tr>
                        `,
                    )}
                </tbody>
            </table>
        </div>
    `;
}
