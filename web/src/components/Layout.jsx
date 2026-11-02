import { useCallback, useEffect, useState } from "react";
import { ToastContext } from "../context/ToastContext";

const TOAST_COLOURS = {
    success: "bg-purple-800 text-white",
    error: "bg-red-800 text-white",
};

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
            <a
                href="#main"
                className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:text-purple-900"
            >
                Skip to content
            </a>
            {navbar}
            <main id="main" tabIndex={-1} className="mx-auto max-w-5xl p-4 pb-24 focus:outline-none">
                {children}
            </main>
            <div
                className="pointer-events-none fixed inset-x-0 bottom-4 flex justify-center px-4"
                role="status"
                aria-live="polite"
            >
                {toast && (
                    <p
                        className={`pointer-events-auto max-w-lg rounded-lg px-4 py-2 shadow-lg ${TOAST_COLOURS[toast.kind] ?? TOAST_COLOURS.success}`}
                    >
                        {toast.text}{" "}
                        <button
                            type="button"
                            className="ml-1 min-h-8 min-w-8 cursor-pointer text-lg"
                            onClick={() => setToast(null)}
                            aria-label="Dismiss message"
                        >
                            ×
                        </button>
                    </p>
                )}
            </div>
        </ToastContext.Provider>
    );
}