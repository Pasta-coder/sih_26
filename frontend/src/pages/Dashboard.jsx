import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { FileText, Plus, Users, CheckCircle, XCircle, Clock, ChevronRight } from 'lucide-react'

export default function Dashboard() {
  const [tenders, setTenders] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/tenders/').then(r => setTenders(r.data)).finally(() => setLoading(false))
  }, [])

  const stats = {
    total: tenders.length,
    active: tenders.filter(t => t.is_active).length,
  }

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Compliance Dashboard</h1>
        <p className="page-subtitle">GeM Procurement Bid Verification — CPCL · Ministry of Petroleum & Natural Gas</p>
      </div>

      <div className="page-content">
        {/* Stats */}
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-icon indigo"><FileText size={20} /></div>
            <div><div className="stat-value">{stats.total}</div><div className="stat-label">Total Tenders</div></div>
          </div>
          <div className="stat-card">
            <div className="stat-icon green"><CheckCircle size={20} /></div>
            <div><div className="stat-value">{stats.active}</div><div className="stat-label">Active Tenders</div></div>
          </div>
          <div className="stat-card">
            <div className="stat-icon amber"><Clock size={20} /></div>
            <div><div className="stat-value">3</div><div className="stat-label">Pending Verifications</div></div>
          </div>
          <div className="stat-card">
            <div className="stat-icon purple">⚡</div>
            <div><div className="stat-value">AI</div><div className="stat-label">Template Engine Active</div></div>
          </div>
        </div>

        {/* Platform description */}
        <div className="card" style={{ marginBottom: 24, background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(16,185,129,0.04))', borderColor: 'var(--border-accent)' }}>
          <div className="flex items-center gap-3 mb-2">
            <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--accent-glow)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>🛡️</div>
            <div>
              <h3 style={{ fontSize: 15, fontWeight: 700 }}>3-Tier Compliance Architecture</h3>
              <p className="text-sm text-muted">Honest integration — real where achievable, transparent where not</p>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginTop: 16 }}>
            {[
              { tier: 'Tier 1', color: 'var(--success)', label: 'Automated', items: 'GST · PAN · EPFO · MCA21', desc: 'Real reseller REST APIs' },
              { tier: 'Tier 2', color: 'var(--warning)', label: 'Manual Redirect', items: 'Udyam · BIS · Startup India', desc: 'Deep-link + officer input' },
              { tier: 'Tier 3', color: 'var(--accent-light)', label: 'Mocked', items: 'DigiLocker · NSIC · OEM · Blacklist', desc: 'Seeded fixtures + admin toggle' },
            ].map(t => (
              <div key={t.tier} style={{ background: 'var(--bg-glass)', borderRadius: 8, padding: '12px 14px', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2 mb-1">
                  <span style={{ fontSize: 11, fontWeight: 700, color: t.color }}>{t.tier}</span>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>·</span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{t.label}</span>
                </div>
                <div style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 2 }}>{t.items}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{t.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Tenders list */}
        <div className="flex items-center justify-between mb-4">
          <h2 style={{ fontSize: 16, fontWeight: 700 }}>Active Tenders</h2>
          <button id="new-tender-btn" className="btn btn-primary btn-sm" onClick={() => navigate('/tenders')}>
            <Plus size={14} /> New Tender
          </button>
        </div>

        {loading ? (
          <div className="loading-center"><div className="spinner" /></div>
        ) : tenders.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: 48 }}>
            <FileText size={40} style={{ color: 'var(--text-muted)', marginBottom: 12, display: 'block', margin: '0 auto 12px' }} />
            <p style={{ color: 'var(--text-muted)' }}>No tenders yet. Create your first tender to start verification.</p>
            <button className="btn btn-primary mt-3" onClick={() => navigate('/tenders')}>Create Tender</button>
          </div>
        ) : (
          <div className="card">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Tender Number</th>
                    <th>Title</th>
                    <th>Department</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {tenders.map(t => (
                    <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/tenders/${t.id}`)}>
                      <td className="font-mono">{t.tender_number}</td>
                      <td style={{ fontWeight: 500 }}>{t.title}</td>
                      <td className="text-muted">{t.department || '—'}</td>
                      <td>
                        <span className={`check-badge ${t.is_active ? 'check-pass' : 'check-na'}`}>
                          {t.is_active ? '● Active' : '○ Inactive'}
                        </span>
                      </td>
                      <td className="text-muted text-sm">{new Date(t.created_at).toLocaleDateString('en-IN')}</td>
                      <td><ChevronRight size={14} color="var(--text-muted)" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
