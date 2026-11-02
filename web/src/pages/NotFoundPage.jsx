import { Link } from "react-router-dom";

export default function NotFoundPage() {
    return (
        <>
            <h1>Page not found</h1>
            <p>There is nothing at this address.</p>
            <p>
                <Link to="/">Back to the catalogue</Link>
            </p>
        </>
    );
}