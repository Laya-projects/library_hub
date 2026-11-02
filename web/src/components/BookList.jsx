import BookCard from "./BookCard";

export default function BookList({ books, search = "", onAdd, onJoin }) {
    return (
        <ul className="book-list">
            {books.map((book) => (
                <li key={book.isbn}>
                    <BookCard
                        book={book}
                        to={{ pathname: `/books/${book.isbn}`, search }}
                        onAdd={onAdd}
                        onJoin={onJoin}
                    />
                </li>
            ))}
        </ul>
    );
}