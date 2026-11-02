import { Link } from "react-router-dom";
import AddItemForm from "../components/AddItemForm";
import { link } from "../ui";

export default function AddItemPage() {
    return (
        <>
            <h1>Add item (librarian)</h1>
            <AddItemForm />
            <p className="mt-4">
                <Link className={link} to="/">.Back to the catalogue</Link>
            </p>
        </>
    );
}