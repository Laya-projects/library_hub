export default function AvailabilityBadge({ available, total, itemType }) {
    const base = "inline-block rounded-xl px-2 py-0.5 text-sm";
    if (itemType === "Reference") {
        return (
            <span className={`${base} bg-gray-200 text-gray-700`}>
                Reference item: read in the library only
            </span>
        );
    }
    const colours = available > 0 ? "bg-green-100 text-green-900" : "bg-red-100 text-red-900";
    return (
        <span className={`${base} ${colours}`}>
            {available} of {total} available
        </span>
    );
}