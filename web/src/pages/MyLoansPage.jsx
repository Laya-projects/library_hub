import { useEffect, useState } from "react";
import { apiGet } from "../api";
import { useMember } from "../context/MemberContext";

function status(daysOverdue) {
    if (daysOverdue <= 0) return "On loan";
    return `OVERDUE (${daysOverdue} ${daysOverdue === 1 ? "day" : "days"})`;
}

export default function MyLoansPage() {
    const {
        currentMember,
        loading: membersLoading,
        error: membersError,
        retry: retryMembers,
    } = useMember();
    const memberId = currentMember?.member_id;

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        if (!memberId) return;
        const controller = new AbortController();
        setLoading(true);
        setError(null);
        apiGet(`/members/${encodeURIComponent(memberId)}/loans`, controller.signal)
            .then((d) => {
                setData(d);
                setLoading(false);
            })
            .catch((err) => {
                if (err.name === "AbortError") return;
                setError(err.message);
                setLoading(false);
            });
        return () => controller.abort();
    }, [memberId, reloadKey]);

    if (!currentMember) {
        if (membersLoading) {
            return (
                <p role="status">
                    <span className="spinner" aria-hidden="true" /> Loading members...
                </p>
            );
        }
        return (
            <p role="alert">
                {membersError ?? "No members found."}{" "}
                <button type="button" onClick={retryMembers}>Retry</button>
            </p>
        );
    }

    return (
        <>
            <h1>My loans</h1>
            {loading && (
                <p role="status">
                    <span className="spinner" aria-hidden="true" /> Loading your loans...
                </p>
            )}
            {!loading && error && (
                <p role="alert">
                    {error}{" "}
                    <button type="button" onClick={() => setReloadKey((k) => k + 1)}>Retry</button>
                </p>
            )}
            {!loading && !error && data && (
                <>
                    <p>
                        {data.member} ({data.membership_type}: up to {data.max_items} items)
                    </p>
                    {data.active.length === 0 ? (
                        <p>You have no active loans.</p>
                    ) : (
                        <div className="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th scope="col">Loan</th>
                                        <th scope="col">Title</th>
                                        <th scope="col">Due</th>
                                        <th scope="col">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.active.map((loan) => (
                                        <tr key={loan.loan_id}>
                                            <td>{loan.loan_id}</td>
                                            <td>{loan.title}</td>
                                            <td>{loan.due_date}</td>
                                            <td>{status(loan.days_overdue)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                    <p>
                        Active loans: {data.active.length} of {data.max_items}
                    </p>
                    <p>Unpaid fines: ₹{data.unpaid_fines}</p>
                </>
            )}
        </>
    );
}