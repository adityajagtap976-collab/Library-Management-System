import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <Link to="/" className="brand">
        Library
      </Link>
      <div className="nav-links">
        <Link to="/">Catalog</Link>
        {role === "member" && <Link to="/account">My Account</Link>}
        {role === "staff" && <Link to="/staff">Staff Dashboard</Link>}
        {!role && <Link to="/login">Login</Link>}
        {role && (
          <button className="link-button" onClick={handleLogout}>
            Log out
          </button>
        )}
      </div>
    </nav>
  );
}
