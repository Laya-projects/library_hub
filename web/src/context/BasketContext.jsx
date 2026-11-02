import { createContext, useContext, useEffect, useReducer } from "react";
import { useMember } from "./MemberContext";
import { basketReducer, INITIAL_BASKET } from "./basketReducer";

const BasketContext = createContext(null);

export function BasketProvider({ children }) {
    const { currentMember } = useMember();
    const [state, dispatch] = useReducer(basketReducer, INITIAL_BASKET);
    const memberId = currentMember?.member_id;

    // A basket belongs to one member: switching member starts a new, empty one.
    useEffect(() => {
        dispatch({ type: "CLEAR" });
    }, [memberId]);

    const limit = currentMember?.max_items ?? 0;

    const value = {
        items: state.items,
        message: state.message,
        limit,
        isFull: state.items.length >= limit,
        has: (isbn) => state.items.some((b) => b.isbn === isbn),
        add: (book) => {
            if (!currentMember) return;
            dispatch({
                type: "ADD",
                book,
                limit,
                membershipType: currentMember.membership_type,
            });
        },
        remove: (isbn) => dispatch({ type: "REMOVE", isbn }),
        clear: () => dispatch({ type: "CLEAR" }),
    };

    return <BasketContext.Provider value={value}>{children}</BasketContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useBasket() {
    const ctx = useContext(BasketContext);
    if (!ctx) throw new Error("useBasket must be used inside BasketProvider");
    return ctx;
}