const numberFormat = new Intl.NumberFormat("en-US");
const compactFormat = new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
});

export const formatNumber = (value) => numberFormat.format(value ?? 0);

export const formatCompact = (value) => compactFormat.format(value ?? 0);

/** Format a signed difference such as "+12" or "-3". */
export function formatDelta(value) {
    if (!value) {
        return "0";
    }

    return `${value > 0 ? "+" : "-"}${numberFormat.format(Math.abs(value))}`;
}

export function formatDate(value) {
    if (!value) {
        return "—";
    }

    return new Date(value).toLocaleDateString("en-GB", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

export function formatDateTime(value) {
    if (!value) {
        return "—";
    }

    return new Date(value).toLocaleString("en-GB", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

const UNITS = [
    ["day", 86_400],
    ["hour", 3_600],
    ["minute", 60],
];

/** Describe how long ago a timestamp was, e.g. "3 hours ago". */
export function timeAgo(value, now = Date.now()) {
    if (!value) {
        return "never";
    }

    const seconds = Math.max(0, Math.round((now - new Date(value).getTime()) / 1000));

    for (const [unit, size] of UNITS) {
        if (seconds >= size) {
            const count = Math.floor(seconds / size);

            return `${count} ${unit}${count === 1 ? "" : "s"} ago`;
        }
    }

    return "just now";
}
