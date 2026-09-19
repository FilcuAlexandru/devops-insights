import { api } from "../core/api.js";
import { html } from "../core/html.js";
import { formatCompact, formatNumber } from "../core/format.js";
import { badge, emptyState, pageHeader } from "../components/ui.js";

function technologyCard(technology) {
    return html`
        <a class="card card--link technology" href="#/technologies/${technology.slug}"
           data-category="${technology.category}">
            ${badge(technology.category)}
            <h3>${technology.name}</h3>
            <p>${technology.description ?? "No description available."}</p>
            <dl class="inline-stats">
                <div>
                    <dt>Repositories</dt>
                    <dd>${formatNumber(technology.repository_count)}</dd>
                </div>
                <div>
                    <dt>Stars</dt>
                    <dd>${formatCompact(technology.total_stars)}</dd>
                </div>
            </dl>
        </a>
    `;
}

export async function render() {
    const technologies = await api.get("/api/technologies");
    const categories = [...new Set(technologies.map((technology) => technology.category))].sort();

    const content = html`
        ${pageHeader({
            eyebrow: "Ecosystem",
            title: "Technologies",
            description: "The DevOps tools and platforms tracked by the platform.",
        })}
        ${technologies.length === 0
            ? emptyState({
                  title: "No technologies yet",
                  message: "Technologies are created by the first collection run.",
                  action: html`<a class="button" href="#/">Go to the dashboard</a>`,
              })
            : html`
                  <div class="chips" role="group" aria-label="Filter by category">
                      <button type="button" class="chip is-active" data-filter="">All</button>
                      ${categories.map(
                          (category) => html`
                              <button type="button" class="chip" data-filter="${category}">
                                  ${category}
                              </button>
                          `,
                      )}
                  </div>
                  <section class="grid grid--cards">${technologies.map(technologyCard)}</section>
              `}
    `;

    return {
        title: "Technologies",
        content,
        mount(root) {
            const chips = root.querySelectorAll(".chip");

            chips.forEach((chip) =>
                chip.addEventListener("click", () => {
                    chips.forEach((other) => other.classList.toggle("is-active", other === chip));

                    root.querySelectorAll(".technology").forEach((card) => {
                        card.hidden = chip.dataset.filter && card.dataset.category !== chip.dataset.filter;
                    });
                }),
            );
        },
    };
}
