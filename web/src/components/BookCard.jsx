import { Link } from "react-router-dom";
import AvailabilityBadge from "./AvailabilityBadge";
import BookActions from "./BookActions";

export default function BookCard({ book, to }) {
    return (
        <article className="book-card">
            <h3>
                <Link to={to}>{book.title}</Link>
            </h3>
            <p>{book.authors.join(", ")}</p>
            <p>
                {book.category} · {book.pages} pages
            </p>
            <AvailabilityBadge
                available={book.available}
                total={book.total}
                itemType={book.item_type}
            />
            <BookActions book={book} />
        </article>
    );
}