import { fieldLabel, input } from "../ui";

export default function SearchBar({ value, onChange }) {
    return (
        <label className={fieldLabel}>
            Search
            <input
                className={input}
                type="search"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Title or author"
            />
        </label>
    );
}