export const API_URL = import.meta.env.VITE_API_URL;

export class ApiError extends Error {
    constructor(status, code, message) {
        super(message);
        this.status = status;
        this.code = code;
    }
}

export async function apiGet(path, signal) {
    let response;
    try {
        response = await fetch(`${API_URL}${path}`, { signal });
    } catch (err) {
        if (err.name === "AbortError") throw err; // cancelled on purpose, not a failure
        throw new ApiError(0, "NetworkError", "Can't reach the library server.");
    }
    const data = await response.json().catch(() => null);
    if (!response.ok) {
        throw new ApiError(
            response.status,
            data?.error ?? "Error",
            data?.message ?? "Something went wrong."
        );
    }
    return data;
}