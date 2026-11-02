export const INITIAL_BASKET = { items: [], message: "" };

export function basketReducer(state, action) {
    switch (action.type) {
        case "ADD": {
            const { book, limit, membershipType } = action;
            const full = `Basket full: ${membershipType}s can borrow ${limit} items.`;

            if (state.items.some((b) => b.isbn === book.isbn)) {
                return { ...state, message: `'${book.title}' is already in your basket.` };
            }
            if (state.items.length >= limit) {
                return { ...state, message: full }; // refused: the message lives in state
            }
            const items = [...state.items, { isbn: book.isbn, title: book.title }];
            return { items, message: items.length >= limit ? full : "" };
        }
        case "REMOVE":
            return {
                items: state.items.filter((b) => b.isbn !== action.isbn),
                message: "",
            };
        case "CLEAR":
            return INITIAL_BASKET;
        default:
            return state;
    }
}