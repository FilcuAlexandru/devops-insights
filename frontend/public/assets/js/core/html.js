/**
 * Safe HTML templating.
 *
 * Every interpolated value is escaped unless it is itself the result of `html` (or `raw`).
 * Repository names and descriptions come from GitHub, so they must never reach the DOM
 * unescaped.
 */

const ESCAPES = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
};

export class SafeHtml {
    constructor(value) {
        this.value = value;
    }

    toString() {
        return this.value;
    }
}

export function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ESCAPES[character]);
}

function toHtml(value) {
    if (value instanceof SafeHtml) {
        return value.value;
    }

    if (Array.isArray(value)) {
        return value.map(toHtml).join("");
    }

    if (value === null || value === undefined || value === false) {
        return "";
    }

    return escapeHtml(value);
}

/** Tagged template that escapes interpolated values. */
export function html(strings, ...values) {
    let result = strings[0];

    values.forEach((value, index) => {
        result += toHtml(value) + strings[index + 1];
    });

    return new SafeHtml(result);
}

/** Mark a string as already-safe markup. Only use it with trusted content. */
export function raw(value) {
    return new SafeHtml(String(value));
}

/** Return the URL if it is http(s), otherwise "#". Prevents `javascript:` links. */
export function safeUrl(value) {
    try {
        const url = new URL(value);

        return url.protocol === "https:" || url.protocol === "http:" ? url.href : "#";
    } catch {
        return "#";
    }
}
