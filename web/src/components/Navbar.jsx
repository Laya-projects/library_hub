import { Link, NavLink } from "react-router-dom";

const linkClass = ({ isActive }) =>
    `inline-flex min-h-11 items-center hover:underline focus-visible:outline-amber-300 ${isActive ? "font-semibold underline" : ""}`;

export default function Navbar({
    basketCount,
    members,
    membersLoading,
    currentMemberId,
    onMemberChange,
}) {
    return (
        <nav
            className="flex flex-wrap items-center gap-x-4 gap-y-1 bg-blue-900 px-4 py-3 text-white"
            aria-label="Main"
        >
            <Link
                to="/"
                className="w-full text-lg font-bold focus-visible:outline-amber-300 sm:mr-auto sm:w-auto"
            >
                LibraryHub Mini
            </Link>
            <NavLink to="/" end className={linkClass}>Catalogue</NavLink>
            <NavLink to="/me" className={linkClass}>My loans</NavLink>
            <NavLink to="/basket" className={linkClass}>Basket ({basketCount})</NavLink>
            <NavLink to="/admin/add" className={linkClass}>Add item</NavLink>
            {membersLoading ? (
                <span>Loading members...</span>
            ) : members.length === 0 ? (
                <span>Members unavailable</span>
            ) : (
                <label className="flex w-full items-center gap-2 sm:w-auto">
                    Member
                    <select
                        className="min-h-11 min-w-0 flex-1 rounded bg-white p-2 text-gray-900 focus-visible:outline-amber-300 sm:flex-none"
                        value={currentMemberId}
                        onChange={(e) => onMemberChange(e.target.value)}
                    >
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