export default function SortSelect({ value, onChange }) {
    return (
        <label>
            Sort{" "}
            <select value={value} onChange={(e) => onChange(e.target.value)}>
                <option value="title">Title</option>
                <option value="pages">Pages</option>
                <option value="category">Category</option>
            </select>
        </label>
    );
}