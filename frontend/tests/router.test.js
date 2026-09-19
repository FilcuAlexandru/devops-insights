import assert from "node:assert/strict";
import { test } from "node:test";

import { matchPattern, matchRoute, parseHash } from "../public/assets/js/core/router.js";

test("parseHash splits path and query", () => {
    assert.deepEqual(parseHash("#/repositories?search=kind&sort=forks"), {
        path: "/repositories",
        query: { search: "kind", sort: "forks" },
    });
});

test("parseHash defaults to the root", () => {
    assert.deepEqual(parseHash(""), { path: "/", query: {} });
    assert.deepEqual(parseHash("#"), { path: "/", query: {} });
});

test("matchPattern extracts and decodes parameters", () => {
    assert.deepEqual(matchPattern("/technologies/:slug", "/technologies/argo%20cd"), {
        slug: "argo cd",
    });
});

test("matchPattern rejects other paths", () => {
    assert.equal(matchPattern("/technologies/:slug", "/technologies"), null);
    assert.equal(matchPattern("/technologies/:slug", "/repositories/x"), null);
    assert.equal(matchPattern("/technologies", "/technologies/x"), null);
});

test("matchRoute returns the first matching route", () => {
    const routes = [{ pattern: "/" }, { pattern: "/repositories/:id" }];

    assert.equal(matchRoute(routes, "/").route, routes[0]);
    assert.equal(matchRoute(routes, "/repositories/7").params.id, "7");
    assert.equal(matchRoute(routes, "/nope"), null);
});
