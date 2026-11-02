import { useEffect, useState } from "react";
import { apiGet } from "../api";
import { useMember } from "../context/MemberContext";
import LoadingSpinner from "../components/LoadingSpinner";
import { btn } from "../ui";

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
        return (
            <>
                <h1>My loans</h1>
                {membersLoading ? (
                    <p role="status">
                        <Spinner /> Loading members...
                    </p>
                ) : (
                    <p role="alert" className="text-red-700">
                        {membersError ?? "No members found."}{" "}
                        <button type="button" className={btn} onClick={retryMembers}>Retry</button>
                    </p>
                )}
            </>
        );
    }

    const cell = "border border-gray-200 px-3 py-2 text-left";

    return (
        <>
            <h1>My loans</h1>
            {loading && (
                <p role="status">
                    <Spinner /> Loading your loans...
                </p>
            )}
            {!loading && error && (
                <p role="alert" className="text-red-700">
                    {error}{" "}
                    <button type="button" className={btn} onClick={() => setReloadKey((k) => k + 1)}>Retry</button>
                </p>
            )}
            {!loading && !error && data && (
                <>
                    <p className="mb-3">
                        {data.member} ({data.membership_type}: up to {data.max_items} items)
                    </p>
                    {data.active.length === 0 ? (
                        <p>You have no active loans.</p>
                    ) : (
                        <div className="overflow-x-auto" role="region" aria-label="Active loans" tabIndex={0}>
                            <table className="w-full border-collapse bg-white">
                                <caption className="sr-only">Your active loans</caption>
                                <thead>
                                    <tr>
                                        <th scope="col" className={cell}>Loan</th>
                                        <th scope="col" className={cell}>Title</th>
                                        <th scope="col" className={cell}>Due</th>
                                        <th scope="col" className={cell}>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.active.map((loan) => (
                                        <tr key={loan.loan_id}>
                                            <td className={cell}>{loan.loan_id}</td>
                                            <td className={cell}>{loan.title}</td>
                                            <td className={cell}>{loan.due_date}</td>
                                            <td className={`${cell} ${loan.days_overdue > 0 ? "font-semibold text-red-700" : ""}`}>
                                                {status(loan.days_overdue)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                    <p className="mt-3">
                        Active loans: {data.active.length} of {data.max_items}
                    </p>
                    <p>Unpaid fines: ₹{data.unpaid_fines}</p>
                </>
            )}
        </>
    );
}