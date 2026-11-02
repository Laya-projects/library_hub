export default function CategoryFilter({ value, onChange, categories }) {
    return (
        <label>
            Category{" "}
            <select value={value} onChange={(e) => onChange(e.target.value)}>
                <option value="">All</option>
                {categories.map((c) => (
                    <option key={c} value={c}>
                        {c}
                    </option>
                ))}
            </select>
        </label>
    );
}