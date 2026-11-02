import AvailabilityBadge from "./AvailabilityBadge";

export default function BookCard({ book, onAdd, onJoin }) {
    const isReference = book.item_type === "Reference";

    return (
        <article className="book-card">
            <h3>{book.title}</h3>
            <p>{book.authors.join(", ")}</p>
            <p>
                {book.category} · {book.pages} pages
            </p>
            <AvailabilityBadge
                available={book.available}
                total={book.total}
                itemType={book.item_type}
            />
            {/* A reference item has no button at all (R1). */}
            {!isReference &&
                (book.available > 0 ? (
                    <button type="button" onClick={() => onAdd?.(book)}>
                        Add to basket
                    </button>
                ) : (
                    <button type="button" onClick={() => onJoin?.(book)}>
                        Join waiting list
                    </button>
                ))}
        </article>
    );
}