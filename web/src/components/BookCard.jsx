import { Link } from "react-router-dom";
import AvailabilityBadge from "./AvailabilityBadge";
import BookActions from "./BookActions";

export default function BookCard({ book, to }) {
    return (
        <article className="relative h-full rounded-lg border border-purple-100 bg-white p-4 has-[a:focus-visible]:outline-3 has-[a:focus-visible]:outline-purple-700">
            <h3 className="text-lg font-semibold">
                <Link
                    to={to}
                    className="no-underline after:absolute after:inset-0 hover:underline focus-visible:outline-none"
                >
                    {book.title}
                </Link>
            </h3>
            <p className="mt-1">{book.authors.join(", ")}</p>
            <p className="mt-1">
                {book.category} · {book.pages} pages
            </p>
            <div className="mt-2">
                <AvailabilityBadge
                    available={book.available}
                    total={book.total}
                    itemType={book.item_type}
                />
            </div>
            <BookActions book={book} />
        </article>
    );
}