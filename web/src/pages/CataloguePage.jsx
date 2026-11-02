import { useEffect, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import { apiGet } from "../api";
import { useBooks } from "../hooks/useBooks";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import SearchBar from "../components/SearchBar";
import CategoryFilter from "../components/CategoryFilter";
import SortSelect from "../components/SortSelect";
import BookList from "../components/BookList";

const SORTS = ["title", "pages", "category"];

export default function CataloguePage({ refreshKey = 0 }) {
    const [searchParams, setSearchParams] = useSearchParams();
    const { search } = useLocation();
    const [categories, setCategories] = useState([]);

    // The URL is the single source of truth for the three controls.
    const query = searchParams.get("q") ?? "";
    const category = searchParams.get("category") ?? "";
    const rawSort = searchParams.get("sort");
    const sort = SORTS.includes(rawSort) ? rawSort : "title";

    function setParam(key, value) {
        setSearchParams(
            (prev) => {
                const next = new URLSearchParams(prev);
                if (value) next.set(key, value);
                else next.delete(key);
                return next;
            },
            { replace: true } // typing must not fill the browser history
        );
    }

    const debouncedQuery = useDebouncedValue(query, 300);
    const { books, loading, error, retry } = useBooks({
        q: debouncedQuery,
        category,
        sort,
        refreshKey,
    });

    useEffect(() => {
        const controller = new AbortController();
        apiGet("/categories", controller.signal)
            .then(setCategories)
            .catch(() => { });
        return () => controller.abort();
    }, [refreshKey]);

    return (
        <>
            <h1>Catalogue</h1>
            <div className="filters">
                <SearchBar value={query} onChange={(v) => setParam("q", v)} />
                <CategoryFilter
                    value={category}
                    onChange={(v) => setParam("category", v)}
                    categories={categories}
                />
                <SortSelect value={sort} onChange={(v) => setParam("sort", v)} />
            </div>

            <div role="status" aria-live="polite">
                {loading && (
                    <p>
                        <span className="spinner" aria-hidden="true" /> Loading catalogue...
                    </p>
                )}
                {!loading && error && (
                    <p>
                        {error} <button onClick={retry}>Retry</button>
                    </p>
                )}
                {!loading && !error && books.length === 0 && (
                    <p>
                        {debouncedQuery.trim()
                            ? `No items match '${debouncedQuery.trim()}'. Try a different word.`
                            : "No items in this category."}
                    </p>
                )}
                {!loading && !error && books.length > 0 && (
                    <p>{books.length === 1 ? "1 result" : `${books.length} results`}</p>
                )}
            </div>

            {!loading && !error && books.length > 0 && (
                <BookList books={books} search={search} />
            )}
        </>
    );
}