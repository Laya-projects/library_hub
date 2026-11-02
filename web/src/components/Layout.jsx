import { useCallback, useEffect, useState } from "react";
import { ToastContext } from "../context/ToastContext";

export default function Layout({ navbar, children }) {
    const [toast, setToast] = useState(null);
    const showToast = useCallback(
        (text, kind = "success") => setToast({ text, kind }),
        []
    );

    useEffect(() => {
        if (!toast) return;
        const id = setTimeout(() => setToast(null), 6000);
        return () => clearTimeout(id);
    }, [toast]);

    return (
        <ToastContext.Provider value={showToast}>
            {navbar}
            <main className="page">{children}</main>
            <div className="toast-area" role="status" aria-live="polite">
                {toast && (
                    <p className={`toast toast-${toast.kind}`}>
                        {toast.text}{" "}
                        <button type="button" onClick={() => setToast(null)} aria-label="Dismiss message">
                            ×
                        </button>
                    </p>
                )}
            </div>
        </ToastContext.Provider>
    );
}