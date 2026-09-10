import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { LayoutDashboard, FileText, ScrollText, Settings, LogOut, Sun, Moon } from 'lucide-react'

export default function Layout() {
  const { user, logout } = useAuth()
  const { dark, toggle } = useTheme()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
    { to: '/tenders', icon: FileText, label: 'Tenders' },
    ...(user?.role === 'admin' ? [{ to: '/audit', icon: ScrollText, label: 'Audit Log' }] : []),
    ...(user?.role === 'admin' ? [{ to: '/admin', icon: Settings, label: 'Admin Panel' }] : []),
  ]

  const initials = user?.full_name?.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) || 'U'

  return (
    <div className="app-layout">
      <aside className="sidebar">
        {/* Brand */}
        <div className="sidebar-logo">
          <div className="brand-name">
            <span className="brand-icon">🔍</span>
            GeM Nirikshan
          </div>
          <div className="brand-sub">Procurement Compliance Platform</div>
        </div>

        {/* Nav */}
        <nav className="sidebar-nav">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={15} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          {/* Dark mode toggle */}
          <button className="theme-toggle" onClick={toggle} id="theme-toggle-btn">
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {dark ? <Moon size={13} /> : <Sun size={13} />}
              {dark ? 'Dark Mode' : 'Light Mode'}
            </span>
            <div className={`toggle-pill ${dark ? 'on' : ''}`}>
              <div className="toggle-knob" />
            </div>
          </button>

          {/* User info */}
          <div className="user-pill">
            <div className="user-avatar">{initials}</div>
            <div className="user-info">
              <div className="name truncate">{user?.full_name}</div>
              <div className="role">{user?.role}</div>
            </div>
            <button className="logout-btn" onClick={handleLogout} title="Logout">
              <LogOut size={13} />
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
