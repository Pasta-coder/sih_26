import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { Settings, ToggleLeft, ToggleRight, RefreshCw } from 'lucide-react'

export default function AdminPanel() {
  const [tenders, setTenders] = useState([])
  const [selected, setSelected] = useState(null)
  const [toggles, setToggles] = useState({})
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState('')

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  useEffect(() => { api.get('/tenders/').then(r => setTenders(r.data)) }, [])

  const loadToggles = (tenderId) => {
    setSelected(tenderId)
    api.get(`/admin/mock-toggle/${tenderId}`).then(r => setToggles(r.data.rule_toggles || {}))
  }

  const saveToggles = async () => {
    setSaving(true)
    await api.patch(`/admin/mock-toggle/${selected}`, toggles)
    setSaving(false)
    showToast('✅ Rule toggles updated! Re-run verification to see score change.')
  }

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Admin Panel</h1>
        <p className="page-subtitle">Manage tender rule toggles and mock service configuration</p>
      </div>

      <div className="page-content">
        {/* Demo Wow Moment Callout */}
        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.1), rgba(16,185,129,0.06))', borderColor: 'var(--border-accent)', marginBottom: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>⚡ Live Re-Verification Demo</h3>
          <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            Toggle a rule below (e.g. enable <strong>EPFO Required</strong>) → go back to a bidder without EPFO registration → click "Run Verification" → watch the score drop and the recommendation update in real time. This is PRD §13 "Wow Moment".
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 20 }}>
          {/* Tender selector */}
          <div className="card">
            <h4 style={{ fontWeight: 700, marginBottom: 12, fontSize: 13 }}>Select Tender</h4>
            {tenders.map(t => (
              <div key={t.id} onClick={() => loadToggles(t.id)}
                style={{ padding: '10px 12px', borderRadius: 8, cursor: 'pointer', marginBottom: 4, background: selected === t.id ? 'var(--accent-glow)' : 'var(--bg-glass)', border: `1px solid ${selected === t.id ? 'var(--border-accent)' : 'var(--border)'}`, transition: 'all 0.2s' }}>
                <div style={{ fontSize: 12, fontWeight: 600, truncate: 'ellipsis' }}>{t.tender_number}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{t.title.slice(0, 30)}...</div>
              </div>
            ))}
          </div>

          {/* Toggle controls */}
          <div className="card">
            {!selected ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                <Settings size={32} style={{ display: 'block', margin: '0 auto 12px', opacity: 0.4 }} />
                Select a tender to configure rule toggles
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h4 style={{ fontWeight: 700 }}>Rule Toggles</h4>
                  <button id="save-toggles-btn" className="btn btn-primary btn-sm" onClick={saveToggles} disabled={saving}>
                    {saving ? <><RefreshCw size={12} /> Saving...</> : 'Save & Apply'}
                  </button>
                </div>

                {Object.entries(toggles).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between" style={{ padding: '14px 0', borderBottom: '1px solid var(--border)' }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 500, textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</div>
                      <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>
                        {key === 'epfo_required' && 'EPFO registration mandatory for all bidders'}
                        {key === 'msme_exemption' && 'MSME bidders exempt from certain requirements'}
                        {key === 'bis_required' && 'BIS certification required (ISI/CRS mark)'}
                        {key === 'make_in_india' && 'Make in India preference applicable'}
                        {key === 'startup_india_eligible' && 'Startup India/DPIIT recognition eligible'}
                      </div>
                    </div>
                    <button
                      id={`toggle-${key}`}
                      type="button"
                      onClick={() => setToggles({ ...toggles, [key]: !val })}
                      style={{ width: 48, height: 26, borderRadius: 13, background: val ? 'var(--accent)' : 'rgba(255,255,255,0.1)', border: 'none', cursor: 'pointer', transition: 'background 0.2s', position: 'relative', flexShrink: 0 }}>
                      <span style={{ position: 'absolute', width: 20, height: 20, background: 'white', borderRadius: '50%', top: 3, left: val ? 25 : 3, transition: 'left 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.3)' }} />
                    </button>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      </div>

      {toast && <div className="toast">{toast}</div>}
    </>
  )
}
