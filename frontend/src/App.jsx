import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import TenderList from './pages/TenderList'
import TenderDetail from './pages/TenderDetail'
import BidderDetail from './pages/BidderDetail'
import AdminPanel from './pages/AdminPanel'
import AuditLog from './pages/AuditLog'
import './index.css'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="loading-center"><div className="spinner" /></div>
  return user ? children : <Navigate to="/login" replace />
}

function AdminRoute({ children }) {
  const { user } = useAuth()
  return user?.role === 'admin' ? children : <Navigate to="/" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="tenders" element={<TenderList />} />
            <Route path="tenders/:id" element={<TenderDetail />} />
            <Route path="bidder/:id" element={<BidderDetail />} />
            {/* F1: /audit calls the admin-only endpoint — guard it like /admin */}
            <Route path="audit" element={<AdminRoute><AuditLog /></AdminRoute>} />
            <Route path="admin" element={<AdminRoute><AdminPanel /></AdminRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
