export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

/** Turn FastAPI error bodies (`{detail: "..."}` or validation lists) into a message. */
function describeError(body, status) {
    const detail = body?.detail;

    if (typeof detail === "string") {
        return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
        return detail.map((item) => item.msg).join("; ");
    }

    return `Request failed with HTTP ${status}.`;
}

async function request(method, path, params) {
    const url = new URL(path, window.location.origin);

    for (const [key, value] of Object.entries(params ?? {})) {
        if (value !== undefined && value !== null && value !== "") {
            url.searchParams.set(key, value);
        }
    }

    let response;

    try {
        response = await fetch(url, { method, headers: { Accept: "application/json" } });
    } catch {
        throw new ApiError("Unable to reach the API. Is the backend running?", 0);
    }

    const body = await response.json().catch(() => null);

    if (!response.ok) {
        throw new ApiError(describeError(body, response.status), response.status);
    }

    return body;
}

export const api = {
    get: (path, params) => request("GET", path, params),
    post: (path, params) => request("POST", path, params),
};
