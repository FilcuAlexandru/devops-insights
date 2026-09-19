import assert from "node:assert/strict";
import { test } from "node:test";

import { renderMarkdown } from "../public/assets/js/core/markdown.js";

const render = (source) => String(renderMarkdown(source));

test("headings and paragraphs", () => {
    assert.equal(render("## Summary\n\nFirst line\nsecond line."), "<h4>Summary</h4><p>First line second line.</p>");
});

test("bullet and numbered lists", () => {
    assert.equal(render("- one\n- two"), "<ul><li>one</li><li>two</li></ul>");
    assert.equal(render("1. one\n2) two"), "<ol><li>one</li><li>two</li></ol>");
});

test("inline bold and code", () => {
    assert.equal(render("Use **bold** and `code`."), "<p>Use <strong>bold</strong> and <code>code</code>.</p>");
});

test("HTML in the model output is escaped", () => {
    const output = render("## <script>alert(1)</script>\n- <img src=x onerror=alert(1)>");

    assert.ok(!output.includes("<script>"));
    assert.ok(!output.includes("<img"));
    assert.ok(output.includes("&lt;script&gt;"));
});

test("a list ends at the next paragraph", () => {
    assert.equal(render("- a\n\ntext"), "<ul><li>a</li></ul><p>text</p>");
});

test("empty input renders nothing", () => {
    assert.equal(render(""), "");
    assert.equal(render(null), "");
});
