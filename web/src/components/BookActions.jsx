export default function BookActions({ book, onAdd, onJoin }) {
    if (book.item_type === "Reference") return null; // R1: no borrow button at all

    return book.available > 0 ? (
        <button type="button" onClick={() => onAdd?.(book)}>
            Add to basket
        </button>
    ) : (
        <button type="button" onClick={() => onJoin?.(book)}>
            Join waiting list
        </button>
    );
}