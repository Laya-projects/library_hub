export default function Layout({ navbar, children }) {
    return (
        <>
            {navbar}
            <main className="page">{children}</main>
        </>
    );
}