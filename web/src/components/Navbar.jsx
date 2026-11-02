import { Link, NavLink } from "react-router-dom";

export default function Navbar({
    basketCount,
    members,
    membersLoading,
    currentMemberId,
    onMemberChange,
}) {
    return (
        <nav className="navbar" aria-label="Main">
            <Link to="/" className="brand">
                LibraryHub Mini
            </Link>
            <NavLink to="/" end>Catalogue</NavLink>
            <NavLink to="/me">My loans</NavLink>
            <NavLink to="/basket">Basket ({basketCount})</NavLink>
            <NavLink to="/admin/add">Add item</NavLink>
            {membersLoading ? (
                <span>Loading members...</span>
            ) : members.length === 0 ? (
                <span>Members unavailable</span>
            ) : (
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
            )}
        </nav>
    );
}