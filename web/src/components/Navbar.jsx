export default function Navbar({ basketCount, members, currentMemberId, onMemberChange }) {
    return (
        <nav className="navbar" aria-label="Main">
            <span className="brand">LibraryHub Mini</span>
            <a href="#catalogue">Catalogue</a>
            <a href="#me">My loans</a>
            <a href="#basket">Basket ({basketCount})</a>
            <label>
                Member{" "}
                <select value={currentMemberId} onChange={(e) => onMemberChange(e.target.value)}>
                    {members.map((m) => (
                        <option key={m.member_id} value={m.member_id}>
                            {m.name}
                        </option>
                    ))}
                </select>
            </label>
        </nav>
    );
}