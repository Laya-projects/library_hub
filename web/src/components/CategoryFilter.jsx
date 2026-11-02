import { fieldLabel, input } from "../ui";

export default function CategoryFilter({ value, onChange, categories }) {
    return (
        <label className={fieldLabel}>
            Category
            <select className={input} value={value} onChange={(e) => onChange(e.target.value)}>
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