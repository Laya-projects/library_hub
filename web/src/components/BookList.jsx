import BookCard from "./BookCard";

export default function BookList({ books }) {
    return (
        <ul className="book-list">
            {books.map((book) => (
                <li key={book.isbn}>
                    <BookCard book={book} />
                </li>
            ))}
        </ul>
    );
}