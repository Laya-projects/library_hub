import { useEffect, useState } from "react";

export function useDebouncedValue(value, delay = 300) {
    const [debounced, setDebounced] = useState(value);

    useEffect(() => {
        const id = setTimeout(() => setDebounced(value), delay);
        return () => clearTimeout(id); // typing again cancels the waiting timer
    }, [value, delay]);

    return debounced;
}