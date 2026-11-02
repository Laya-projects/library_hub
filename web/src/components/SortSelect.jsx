import { fieldLabel, input } from "../ui";

export default function SortSelect({ value, onChange }) {
    return (
        <label className={fieldLabel}>
            Sort
            <select className={input} value={value} onChange={(e) => onChange(e.target.value)}>
                <option value="title">Title</option>
                <option value="pages">Pages</option>
                <option value="category">Category</option>
            </select>
        </label>
    );
}