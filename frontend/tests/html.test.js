import assert from "node:assert/strict";
import { test } from "node:test";

import { escapeHtml, html, raw, safeUrl } from "../public/assets/js/core/html.js";

test("interpolated text is escaped", () => {
    const result = html`<p>${'<img src=x onerror="alert(1)">'}</p>`;

    assert.equal(String(result), "<p>&lt;img src=x onerror=&quot;alert(1)&quot;&gt;</p>");
});

test("attribute values cannot break out of their quotes", () => {
    const result = html`<a title="${'" onmouseover="x'}">link</a>`;

    assert.equal(String(result), '<a title="&quot; onmouseover=&quot;x">link</a>');
});

test("nested templates are not escaped twice", () => {
    const inner = html`<b>${"a & b"}</b>`;

    assert.equal(String(html`<p>${inner}</p>`), "<p><b>a &amp; b</b></p>");
});

test("arrays are joined and their items escaped", () => {
    const items = ["<a>", html`<i>ok</i>`];

    assert.equal(String(html`<ul>${items}</ul>`), "<ul>&lt;a&gt;<i>ok</i></ul>");
});

test("null, undefined and false render nothing", () => {
    assert.equal(String(html`[${null}${undefined}${false}]`), "[]");
});

test("zero and empty strings are rendered as values", () => {
    assert.equal(String(html`[${0}]`), "[0]");
});

test("raw marks trusted markup", () => {
    assert.equal(String(html`${raw("<hr>")}`), "<hr>");
});

test("escapeHtml handles all special characters", () => {
    assert.equal(escapeHtml(`&<>"'`), "&amp;&lt;&gt;&quot;&#39;");
});

test("safeUrl only allows http and https", () => {
    assert.equal(safeUrl("https://github.com/a/b"), "https://github.com/a/b");
    assert.equal(safeUrl("http://localhost:3000"), "http://localhost:3000/");
    assert.equal(safeUrl("javascript:alert(1)"), "#");
    assert.equal(safeUrl("not a url"), "#");
});
