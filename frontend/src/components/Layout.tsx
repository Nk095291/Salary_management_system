import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="header-brand">
          <h1>Salary Management</h1>
          <span className="header-sub">HR Portal</span>
        </div>
        <nav className="nav">
          <NavLink to="/profile" className={({ isActive }) => (isActive ? 'active' : '')}>
            Profile
          </NavLink>
          <NavLink to="/employees" className={({ isActive }) => (isActive ? 'active' : '')}>
            Employees
          </NavLink>
          <NavLink to="/insights" className={({ isActive }) => (isActive ? 'active' : '')}>
            Insights
          </NavLink>
          <button type="button" className="btn btn-ghost" onClick={handleLogout}>
            Logout
          </button>
        </nav>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
