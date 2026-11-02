import { createContext, useContext, useEffect, useState } from "react";
import { apiGet } from "../api";

const MemberContext = createContext(null);

export function MemberProvider({ children }) {
    const [members, setMembers] = useState([]);
    const [currentId, setCurrentId] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError(null);
        apiGet("/members", controller.signal)
            .then((data) => {
                setMembers(data);
                setCurrentId((id) => id || data[0]?.member_id || "");
                setLoading(false);
            })
            .catch((err) => {
                if (err.name === "AbortError") return;
                setError(err.message);
                setLoading(false);
            });
        return () => controller.abort();
    }, [reloadKey]);

    const currentMember = members.find((m) => m.member_id === currentId) ?? null;

    const value = {
        members,
        currentMember,
        setCurrentMemberId: setCurrentId,
        loading,
        error,
        retry: () => setReloadKey((k) => k + 1),
    };

    return <MemberContext.Provider value={value}>{children}</MemberContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useMember() {
    const ctx = useContext(MemberContext);
    if (!ctx) throw new Error("useMember must be used inside MemberProvider");
    return ctx;
}