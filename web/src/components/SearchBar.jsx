export default function SearchBar({ value, onChange }) {
    return (
        <label>
            Search{" "}
            <input
                type="search"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Title or author"
            />
        </label>
    );
}