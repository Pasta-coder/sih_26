import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LayoutDashboard, FileText, Users, ScrollText, Settings, LogOut, Shield } from 'lucide-react'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
    { to: '/tenders', icon: FileText, label: 'Tenders' },
    { to: '/audit', icon: ScrollText, label: 'Audit Log' },
    ...(user?.role === 'admin' ? [{ to: '/admin', icon: Settings, label: 'Admin Panel' }] : []),
  ]

  const initials = user?.full_name?.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) || 'U'

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h2>GeM Compliance</h2>
          <p>AI Bid Verification Platform</p>
          <span className="gem-badge">⚡ SIH 2026 · PS-26100</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-pill">
            <div className="user-avatar">{initials}</div>
            <div className="user-info">
              <div className="name truncate">{user?.full_name}</div>
              <div className="role">{user?.role}</div>
            </div>
            <button className="logout-btn" onClick={handleLogout} title="Logout">
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* Page content */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
