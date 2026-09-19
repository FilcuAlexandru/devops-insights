import assert from "node:assert/strict";
import { test } from "node:test";

import { formatDelta, formatNumber, timeAgo } from "../public/assets/js/core/format.js";

const NOW = Date.parse("2026-09-19T12:00:00Z");

test("numbers use thousands separators", () => {
    assert.equal(formatNumber(1234567), "1,234,567");
    assert.equal(formatNumber(null), "0");
});

test("deltas carry their sign", () => {
    assert.equal(formatDelta(12), "+12");
    assert.equal(formatDelta(-1200), "-1,200");
    assert.equal(formatDelta(0), "0");
});

test("timeAgo picks the largest fitting unit", () => {
    assert.equal(timeAgo("2026-09-19T11:59:40Z", NOW), "just now");
    assert.equal(timeAgo("2026-09-19T11:59:00Z", NOW), "1 minute ago");
    assert.equal(timeAgo("2026-09-19T09:00:00Z", NOW), "3 hours ago");
    assert.equal(timeAgo("2026-09-17T12:00:00Z", NOW), "2 days ago");
});

test("timeAgo without a value", () => {
    assert.equal(timeAgo(null, NOW), "never");
});
