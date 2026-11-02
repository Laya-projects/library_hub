import { createContext, useContext } from "react";

export const ToastContext = createContext(() => { });

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
    return useContext(ToastContext);
}