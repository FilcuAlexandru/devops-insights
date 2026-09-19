import { api } from "../core/api.js";
import { config } from "../core/config.js";
import { html, safeUrl } from "../core/html.js";
import { badge, pageHeader, sectionHeader } from "../components/ui.js";

/** Credentials are the same everywhere on purpose: this is a personal lab project. */
const CREDENTIALS = "admin / admin";

function components(status) {
    const { links } = config;

    return [
        {
            name: "Web application",
            description: "This user interface (nginx).",
            url: window.location.origin,
            credentials: "No login",
        },
        {
            name: "Backend API",
            description: "FastAPI. Interactive documentation.",
            url: links.apiDocs,
            credentials: "No login",
            state: status.database_ok ? badge("database ok", "success") : badge("database down", "danger"),
        },
        {
            name: "Grafana",
            description: "Dashboards for application metrics.",
            url: links.grafana,
            credentials: CREDENTIALS,
        },
        {
            name: "Prometheus",
            description: "Metrics storage and queries.",
            url: links.prometheus,
            credentials: CREDENTIALS,
        },
        {
            name: "Argo CD",
            description: "GitOps delivery (Kubernetes and OpenShift only).",
            url: links.argocd,
            credentials: CREDENTIALS,
        },
        {
            name: "Ollama",
            description: "Local model runtime used for AI analysis.",
            url: links.ollama,
            credentials: "No login",
            state: status.ollama.ready
                ? badge(`${status.ollama.model} ready`, "success")
                : badge(status.ollama.available ? "model missing" : "unreachable", "warning"),
        },
        {
            name: "PostgreSQL",
            description: "Database `devops_insights`. Connect with any SQL client.",
            address: links.postgres,
            credentials: CREDENTIALS,
        },
    ];
}

function row(component) {
    const address = component.url || component.address;

    return html`
        <tr>
            <td>
                <strong>${component.name}</strong>
                <p class="table__subtitle">${component.description}</p>
            </td>
            <td>
                ${!address && badge("not available here")}
                ${component.url &&
                html`<a href="${safeUrl(component.url)}" target="_blank" rel="noopener noreferrer">
                    ${component.url}
                </a>`}
                ${!component.url && component.address && html`<code>${component.address}</code>`}
            </td>
            <td>${address ? component.credentials : "—"}</td>
            <td>${component.state ?? ""}</td>
        </tr>
    `;
}

export async function render() {
    const status = await api.get("/api/status");

    const content = html`
        ${pageHeader({
            eyebrow: "Operations",
            title: "Platform",
            description: `Every component of this ${config.environment} deployment, with its address and login.`,
        })}
        <section class="card">
            ${sectionHeader({
                title: "Components",
                description: `Version ${status.version} · ${status.environment} environment`,
            })}
            <div class="table-wrap">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Component</th>
                            <th>Address</th>
                            <th>Login</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>${components(status).map(row)}</tbody>
                </table>
            </div>
        </section>
    `;

    return { title: "Platform", content };
}
