import { apiPost } from "../api";
import { useBasket } from "../context/BasketContext";
import { useMember } from "../context/MemberContext";
import { useToast } from "../context/ToastContext";

export default function BookActions({ book }) {
    const { currentMember } = useMember();
    const basket = useBasket();
    const showToast = useToast();

    if (book.item_type === "Reference") return null; // R1: no borrow button at all

    async function joinWaitingList() {
        if (!currentMember) return;
        try {
            const { position } = await apiPost("/reservations", {
                member_id: currentMember.member_id,
                isbn: book.isbn,
            });
            showToast(
                `${currentMember.name} is #${position} on the waiting list for '${book.title}'.`
            );
        } catch (err) {
            showToast(err.message, "error"); // the server's words, unchanged
        }
    }

    if (book.available > 0) {
        const inBasket = basket.has(book.isbn);
        return (
            <button
                type="button"
                onClick={() => basket.add(book)}
                disabled={!currentMember || inBasket || basket.isFull}
            >
                {inBasket ? "In basket" : "Add to basket"}
            </button>
        );
    }

    return (
        <button type="button" onClick={joinWaitingList} disabled={!currentMember}>
            Join waiting list
        </button>
    );
}