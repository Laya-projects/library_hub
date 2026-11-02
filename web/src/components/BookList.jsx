import BookCard from "./BookCard";

export default function BookList({ books, search = "" }) {
    return (
        <ul className="book-list">
            {books.map((book) => (
                <li key={book.isbn}>
                    <BookCard book={book} to={{ pathname: `/books/${book.isbn}`, search }} />
                </li>
            ))}
        </ul>
    );
}