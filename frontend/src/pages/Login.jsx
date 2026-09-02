import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Shield, Lock, Mail, Eye, EyeOff, AlertCircle } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials. Try admin@cpcl.gov.in / Admin@1234')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="logo-ring"><Shield size={28} color="white" /></div>
          <h1>GeM Compliance Platform</h1>
          <p>AI-Powered Bid Verification · SIH 2026 · PS-26100</p>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            Ministry of Petroleum & Natural Gas — CPCL
          </p>
        </div>

        {error && (
          <div style={{ background: 'var(--danger-bg)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 16, display: 'flex', gap: 8, alignItems: 'flex-start' }}>
            <AlertCircle size={14} color="var(--danger)" style={{ marginTop: 2, flexShrink: 0 }} />
            <span style={{ fontSize: 13, color: 'var(--danger)' }}>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                id="login-email"
                className="input"
                style={{ paddingLeft: 36 }}
                type="email" value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="officer@cpcl.gov.in"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                id="login-password"
                className="input"
                style={{ paddingLeft: 36, paddingRight: 40 }}
                type={showPw ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
              <button type="button" onClick={() => setShowPw(!showPw)}
                style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>

          <button id="login-submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 4 }} disabled={loading} type="submit">
            {loading ? <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Signing in...</> : 'Sign In →'}
          </button>
        </form>

        <div style={{ marginTop: 24, padding: '16px', background: 'var(--bg-glass)', borderRadius: 8, border: '1px solid var(--border)' }}>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>DEMO CREDENTIALS</p>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'monospace' }}>Admin: admin@cpcl.gov.in / Admin@1234</p>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'monospace' }}>Officer: officer@cpcl.gov.in / Officer@1234</p>
        </div>
      </div>
    </div>
  )
}
