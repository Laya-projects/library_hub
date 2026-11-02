import BookCard from "./BookCard";

export default function BookList({ books, search = "" }) {
    return (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {books.map((book) => (
                <li key={book.isbn}>
                    <BookCard book={book} to={{ pathname: `/books/${book.isbn}`, search }} />
                </li>
            ))}
        </ul>
    );
}