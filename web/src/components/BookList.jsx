import BookCard from "./BookCard";

export default function BookList({ books, onAdd, onJoin }) {
    return (
        <ul className="book-list">
            {books.map((book) => (
                <li key={book.isbn}>
                    <BookCard book={book} onAdd={onAdd} onJoin={onJoin} />
                </li>
            ))}
        </ul>
    );
}