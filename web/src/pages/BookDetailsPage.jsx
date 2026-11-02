import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { apiGet } from "../api";
import AvailabilityBadge from "../components/AvailabilityBadge";
import BookActions from "../components/BookActions";

export default function BookDetailsPage() {
    const { isbn } = useParams();
    const { search } = useLocation(); // the search the member came from
    const [book, setBook] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError(null);
        apiGet(`/books/${encodeURIComponent(isbn)}`, controller.signal)
            .then((data) => {
                setBook(data);
                setLoading(false);
            })
            .catch((err) => {
                if (err.name === "AbortError") return;
                setBook(null);
                setError(err);
                setLoading(false);
            });
        return () => controller.abort();
    }, [isbn, reloadKey]);

    const back = (
        <p>
            <Link to={{ pathname: "/", search }}>← Back to results</Link>
        </p>
    );

    if (loading) {
        return (
            <>
                {back}
                <p role="status">
                    <span className="spinner" aria-hidden="true" /> Loading book...
                </p>
            </>
        );
    }

    if (error) {
        return (
            <>
                {back}
                <p role="alert">{error.message}</p>
                {error.status === 0 && (
                    <button onClick={() => setReloadKey((k) => k + 1)}>Retry</button>
                )}
            </>
        );
    }

    // The brief words these two rows differently, so the page matches each one.
    const copies =
        book.available > 0
            ? `${book.available} of ${book.total} copies available`
            : `${book.available} of ${book.total} available`;

    return (
        <>
            {back}
            <article className="details">
                <h1>{book.title}</h1>
                <p>{book.authors.join(", ")}</p>
                <p>
                    {book.category} · {book.item_type} · {book.pages} pages
                </p>
                <p>ISBN {book.isbn}</p>
                {book.item_type !== "Reference" && <p>{copies}</p>}
                <AvailabilityBadge
                    available={book.available}
                    total={book.total}
                    itemType={book.item_type}
                />
                <BookActions book={book} />
            </article>
        </>
    );
}