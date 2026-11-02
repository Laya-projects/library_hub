export default function AvailabilityBadge({ available, total, itemType }) {
    if (itemType === "Reference") {
        return <span className="badge badge-ref">Reference item: read in the library only</span>;
    }
    const style = available > 0 ? "badge badge-ok" : "badge badge-none";
    return (
        <span className={style}>
            {available} of {total} available
        </span>
    );
}