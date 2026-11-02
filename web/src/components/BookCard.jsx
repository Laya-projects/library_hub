import AvailabilityBadge from "./AvailabilityBadge";

export default function BookCard({ book }) {
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
        </article>
    );
}