import { useEffect, useState } from "react";
import { apiGet } from "../api";

export function useBooks({ q, category, sort, refreshKey = 0 }) {
    const [books, setBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError(null);

        const params = new URLSearchParams();
        if (q.trim()) params.set("q", q.trim());
        if (category) params.set("category", category);
        params.set("sort", sort);

        apiGet(`/books?${params}`, controller.signal)
            .then((data) => {
                setBooks(data);
                setLoading(false);
            })
            .catch((err) => {
                if (err.name === "AbortError") return; // a newer request replaced this one
                setError(err.message);
                setLoading(false);
            });

        return () => controller.abort(); // cleanup: cancel the old request
    }, [q, category, sort, reloadKey, refreshKey]);

    return { books, loading, error, retry: () => setReloadKey((k) => k + 1) };
}