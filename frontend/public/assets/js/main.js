import { app } from "./core/app.js";
import { createRouter } from "./core/router.js";

const routes = [
    { pattern: "/", nav: "dashboard", load: () => import("./pages/dashboard.js") },
    { pattern: "/technologies", nav: "technologies", load: () => import("./pages/technologies.js") },
    {
        pattern: "/technologies/:slug",
        nav: "technologies",
        load: () => import("./pages/technology-detail.js"),
    },
    { pattern: "/repositories", nav: "repositories", load: () => import("./pages/repositories.js") },
    {
        pattern: "/repositories/:id",
        nav: "repositories",
        load: () => import("./pages/repository-detail.js"),
    },
    { pattern: "/platform", nav: "platform", load: () => import("./pages/platform.js") },
];

function highlightNavigation(active) {
    document.querySelectorAll("[data-nav]").forEach((link) => {
        const isActive = link.dataset.nav === active;

        link.classList.toggle("is-active", isActive);

        if (isActive) {
            link.setAttribute("aria-current", "page");
        } else {
            link.removeAttribute("aria-current");
        }
    });
}

const router = createRouter({
    routes,
    outlet: document.getElementById("app"),
    notFoundPage: () => import("./pages/not-found.js"),
    errorPage: () => import("./pages/error.js"),
    onNavigate: highlightNavigation,
});

app.refresh = router.refresh;
router.start();
