import { Link } from "react-router-dom";
import AddItemForm from "../components/AddItemForm";

export default function AddItemPage() {
    return (
        <>
            <h1>Add item (librarian)</h1>
            <AddItemForm />
            <p>
                <Link to="/">Back to the catalogue</Link>
            </p>
        </>
    );
}