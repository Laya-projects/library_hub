import { useState } from "react";
import { Link } from "react-router-dom";
import { apiPost } from "../api";
import { useBasket } from "../context/BasketContext";
import { useMember } from "../context/MemberContext";
import { useToast } from "../context/ToastContext";

export default function BasketPage() {
    const { currentMember } = useMember();
    const basket = useBasket();
    const showToast = useToast();
    const [submitting, setSubmitting] = useState(false);
    const [results, setResults] = useState([]);

    const memberId = currentMember?.member_id;
    // Results from another member's checkout are never shown.
    const mine = results.filter((r) => r.memberId === memberId);
    const successes = mine.filter((r) => r.ok);
    const failures = Object.fromEntries(
        mine.filter((r) => !r.ok).map((r) => [r.isbn, r.text])
    );

    async function checkout() {
        if (!currentMember || submitting || basket.items.length === 0) return;
        setSubmitting(true);
        setResults([]);
        const outcomes = [];
        try {
            for (const item of basket.items) {
                // One after another, never in parallel: each answer is the true state.
                try {
                    const loan = await apiPost("/loans", {
                        member_id: memberId,
                        isbn: item.isbn,
                    });
                    basket.remove(item.isbn);
                    outcomes.push({
                        memberId,
                        isbn: item.isbn,
                        ok: true,
                        text: `Borrowed ${item.title}. Due ${loan.due_date}.`,
                    });
                } catch (err) {
                    outcomes.push({ memberId, isbn: item.isbn, ok: false, text: err.message });
                }
                setResults([...outcomes]);
            }
        } finally {
            setSubmitting(false);
        }
        const borrowed = outcomes.filter((o) => o.ok);
        if (borrowed.length > 0) showToast(borrowed.map((o) => o.text).join(" "));
    }

    return (
        <>
            <h1>Basket</h1>
            {currentMember && (
                <p>
                    {currentMember.name} can borrow up to {basket.limit} items (
                    {basket.items.length} in the basket).
                </p>
            )}

            {basket.items.length === 0 && successes.length === 0 && (
                <p>
                    Your basket is empty. <Link to="/">Browse the catalogue</Link>
                </p>
            )}

            {basket.items.length > 0 && (
                <ul className="basket-list">
                    {basket.items.map((item) => (
                        <li key={item.isbn}>
                            <span>{item.title}</span>
                            <button
                                type="button"
                                onClick={() => basket.remove(item.isbn)}
                                disabled={submitting}
                                aria-label={`Remove ${item.title}`}
                            >
                                Remove
                            </button>
                            {failures[item.isbn] && (
                                <p className="field-error" role="alert">
                                    {failures[item.isbn]}
                                </p>
                            )}
                        </li>
                    ))}
                </ul>
            )}

            <div role="status" aria-live="polite">
                {successes.map((r) => (
                    <p key={r.isbn} className="success">
                        {r.text}
                    </p>
                ))}
            </div>

            {basket.items.length > 0 && (
                <div className="basket-actions">
                    <button type="button" onClick={checkout} disabled={submitting}>
                        {submitting ? "Borrowing..." : "Borrow"}
                    </button>
                    <button type="button" onClick={basket.clear} disabled={submitting}>
                        Clear basket
                    </button>
                </div>
            )}

            {successes.length > 0 && (
                <p>
                    <Link to="/">Back to the catalogue</Link>
                </p>
            )}
        </>
    );
}