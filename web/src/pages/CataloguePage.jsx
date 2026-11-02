import { useEffect, useState } from "react";
import { apiGet } from "../api";
import { useBooks } from "../hooks/useBooks";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import SearchBar from "../components/SearchBar";
import CategoryFilter from "../components/CategoryFilter";
import SortSelect from "../components/SortSelect";
import BookList from "../components/BookList";

export default function CataloguePage({ refreshKey = 0 }) {
    const [query, setQuery] = useState("");
    const [category, setCategory] = useState("");
    const [sort, setSort] = useState("title");
    const [categories, setCategories] = useState([]);

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
            .catch(() => { }); // the filter just stays empty if this fails
        return () => controller.abort();
    }, [refreshKey]);

    return (
        <>
            <h1>Catalogue</h1>
            <div className="filters">
                <SearchBar value={query} onChange={setQuery} />
                <CategoryFilter value={category} onChange={setCategory} categories={categories} />
                <SortSelect value={sort} onChange={setSort} />
            </div>

            <div role="status" aria-live="polite">
                {loading && <p><span className="spinner" aria-hidden="true" /> Loading catalogue...</p>}
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

            {!loading && !error && books.length > 0 && <BookList books={books} />}
        </>
    );
}