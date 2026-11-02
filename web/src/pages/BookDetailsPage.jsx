import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { apiGet } from "../api";
import AvailabilityBadge from "../components/AvailabilityBadge";
import BookActions from "../components/BookActions";
import LoadingSpinner from "../components/LoadingSpinner";
import { btn, card, link } from "../ui";

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
        <p className="mb-3">
            <Link className={link} to={{ pathname: "/", search }}>← Back to results</Link>
        </p>
    );

    if (loading) {
        return (
            <>
                {back}
                <p role="status">
                    <LoadingSpinner /> Loading book...
                </p>
            </>
        );
    }

    if (error) {
        return (
            <>
                {back}
                <p role="alert" className="text-red-700">{error.message}</p>
                {error.status === 0 && (
                    <button type="button" className={`${btn} mt-2`} onClick={() => setReloadKey((k) => k + 1)}>
                        Retry
                    </button>
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
            <article className={`${card} max-w-lg`}>
                <h1>{book.title}</h1>
                <p>{book.authors.join(", ")}</p>
                <p className="mt-1">
                    {book.category} · {book.item_type} · {book.pages} pages
                </p>
                <p className="mt-1">ISBN {book.isbn}</p>
                {book.item_type !== "Reference" && <p className="mt-1">{copies}</p>}
                <div className="mt-2">
                    <AvailabilityBadge
                        available={book.available}
                        total={book.total}
                        itemType={book.item_type}
                    />
                </div>
                <BookActions book={book} />
            </article>
        </>
    );
}