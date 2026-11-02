import { useState } from "react";
import { apiPost } from "../api";
import { btn, input } from "../ui";

const EMPTY = {
    isbn: "",
    title: "",
    authors: "",
    copies: "1",
    itemType: "Book",
    category: "",
    pages: "",
};

// Early checks for the member's comfort. The server checks all of this again (R9).
function validate(v) {
    const errors = {};
    if (!/^[0-9]{13}$/.test(v.isbn)) errors.isbn = "ISBN must be exactly 13 digits.";
    if (!v.title.trim()) errors.title = "Title is required.";
    const copies = Number(v.copies);
    if (v.copies.trim() === "" || !Number.isInteger(copies) || copies < 1) {
        errors.copies = "Copies must be a whole number, at least 1.";
    }
    if (v.pages.trim() !== "") {
        const pages = Number(v.pages);
        if (!Number.isInteger(pages) || pages < 1) {
            errors.pages = "Pages must be a whole number above 0.";
        }
    }
    return errors;
}

function Field({ id, label, error, children }) {
    return (
        <div className="grid gap-1">
            <label htmlFor={id} className="text-sm font-medium">{label}</label>
            {children}
            {error && (
                <p id={`${id}-error`} className="text-red-700">
                    {error}
                </p>
            )}
        </div>
    );
}

export default function AddItemForm({ onCreated }) {
    const [values, setValues] = useState(EMPTY);
    const [touched, setTouched] = useState({});
    const [submitting, setSubmitting] = useState(false);
    const [serverError, setServerError] = useState("");
    const [success, setSuccess] = useState("");

    const errors = validate(values);
    const isValid = Object.keys(errors).length === 0;

    // Everything an input needs, so each input below stays short.
    function inputProps(name) {
        return {
            id: name,
            className: input,
            value: values[name],
            onChange: (e) => {
                setValues((v) => ({ ...v, [name]: e.target.value }));
                setTouched((t) => ({ ...t, [name]: true }));
                setSuccess("");
            },
            onBlur: () => setTouched((t) => ({ ...t, [name]: true })),
            "aria-invalid": touched[name] && errors[name] ? "true" : "false",
            "aria-describedby": touched[name] && errors[name] ? `${name}-error` : undefined,
        };
    }

    const shown = (name) => (touched[name] ? errors[name] : undefined);

    async function handleSubmit(e) {
        e.preventDefault();
        if (!isValid || submitting) return;
        setSubmitting(true);
        setServerError("");
        setSuccess("");

        const body = {
            isbn: values.isbn,
            title: values.title.trim(),
            copies: Number(values.copies),
            item_type: values.itemType,
            authors: values.authors.split(",").map((a) => a.trim()).filter(Boolean),
        };
        if (values.category.trim()) body.category = values.category.trim();
        if (values.pages.trim()) body.pages = Number(values.pages);

        try {
            const book = await apiPost("/books", body);
            setSuccess(`Added '${book.title}' to the catalogue.`);
            setValues(EMPTY);
            setTouched({});
            onCreated?.(book);
        } catch (err) {
            setServerError(err.message); // the server's own words, unchanged
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <form onSubmit={handleSubmit} className="grid max-w-md gap-3" noValidate>
            <Field id="isbn" label="ISBN (13 digits)" error={shown("isbn")}>
                <input type="text" inputMode="numeric" {...inputProps("isbn")} />
            </Field>
            <Field id="title" label="Title" error={shown("title")}>
                <input type="text" {...inputProps("title")} />
            </Field>
            <Field id="authors" label="Authors (separate with commas)">
                <input type="text" {...inputProps("authors")} />
            </Field>
            <Field id="copies" label="Copies" error={shown("copies")}>
                <input type="number" min="1" {...inputProps("copies")} />
            </Field>
            <Field id="itemType" label="Type">
                <select {...inputProps("itemType")}>
                    <option value="Book">Book</option>
                    <option value="Magazine">Magazine</option>
                    <option value="Reference">Reference</option>
                </select>
            </Field>
            <Field id="category" label="Category (optional)">
                <input type="text" {...inputProps("category")} />
            </Field>
            <Field id="pages" label="Pages (optional)" error={shown("pages")}>
                <input type="number" min="1" {...inputProps("pages")} />
            </Field>

            <div role="status" aria-live="polite">
                {serverError && <p className="text-red-700">{serverError}</p>}
                {success && <p className="text-green-700">{success}</p>}
            </div>

            <button type="submit" className={`${btn} justify-self-start`} disabled={!isValid || submitting}>
                {submitting ? "Adding..." : "Add item"}
            </button>
        </form>
    );
}