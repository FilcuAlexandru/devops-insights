/** Split "#/path?a=1" into a path and a query object. */
export function parseHash(hash) {
    const value = hash.replace(/^#/, "") || "/";
    const [path, queryString = ""] = value.split("?");

    return {
        path: path || "/",
        query: Object.fromEntries(new URLSearchParams(queryString)),
    };
}

/** Match "/repositories/:id" against a path. Returns the params, or null. */
export function matchPattern(pattern, path) {
    const patternParts = pattern.split("/").filter(Boolean);
    const pathParts = path.split("/").filter(Boolean);

    if (patternParts.length !== pathParts.length) {
        return null;
    }

    const params = {};

    for (const [index, part] of patternParts.entries()) {
        if (part.startsWith(":")) {
            params[part.slice(1)] = decodeURIComponent(pathParts[index]);
        } else if (part !== pathParts[index]) {
            return null;
        }
    }

    return params;
}

/** Find the first route whose pattern matches the path. */
export function matchRoute(routes, path) {
    for (const route of routes) {
        const params = matchPattern(route.pattern, path);

        if (params) {
            return { route, params };
        }
    }

    return null;
}

/**
 * Hash-based router.
 *
 * A route is `{ pattern, nav, load }`, where `load()` imports a page module. A page module
 * exports `render({ params, query })` returning `{ title, content, mount? }`; `mount(root)`
 * may return a cleanup function that runs before the next navigation.
 *
 * `notFoundPage` loads the page shown for unknown paths and `errorPage` loads a module that
 * exports `renderError(error)`; its markup may contain a `[data-retry]` button.
 */
export function createRouter({ routes, outlet, notFoundPage, errorPage, onNavigate }) {
    let cleanup = null;
    let navigation = 0;

    async function show(load, context) {
        const current = ++navigation;

        cleanup?.();
        cleanup = null;
        outlet.setAttribute("aria-busy", "true");

        try {
            const page = await load();
            const view = await page.render(context);

            if (current !== navigation) {
                return;
            }

            document.title = `${view.title} · DevOps Insights`;
            outlet.innerHTML = String(view.content);
            cleanup = view.mount?.(outlet) ?? null;
        } catch (error) {
            if (current !== navigation) {
                return;
            }

            console.error(error);
            const { renderError } = await errorPage();
            outlet.innerHTML = String(renderError(error));
            outlet.querySelector("[data-retry]")?.addEventListener("click", navigate);
        } finally {
            if (current === navigation) {
                outlet.removeAttribute("aria-busy");
            }
        }
    }

    async function navigate() {
        const { path, query } = parseHash(window.location.hash);
        const match = matchRoute(routes, path);

        onNavigate?.(match?.route.nav ?? null);

        if (match) {
            await show(match.route.load, { params: match.params, query });
        } else {
            await show(notFoundPage, { params: {}, query: {} });
        }
    }

    return {
        start() {
            window.addEventListener("hashchange", () => {
                window.scrollTo({ top: 0 });
                navigate();
            });
            navigate();
        },
        refresh: navigate,
    };
}
