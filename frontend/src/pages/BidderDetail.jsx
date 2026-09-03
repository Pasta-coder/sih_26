import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import { Play, RefreshCw, ExternalLink, Edit2, Shield, Download } from 'lucide-react'

const RISK_CLASS = { Low: 'risk-low', Medium: 'risk-medium', High: 'risk-high', Critical: 'risk-critical' }
const STATUS_INFO = {
  pass: { cls: 'check-pass', label: '✅ Pass' },
  fail: { cls: 'check-fail', label: '❌ Fail' },
  manual_review: { cls: 'check-manual', label: '⏳ Manual Review' },
  not_applicable: { cls: 'check-na', label: '➖ N/A' },
  pending: { cls: 'check-pending', label: '⏳ Pending' },
}
const TIER_LABEL = { tier1: 'Tier 1 · Auto', tier2: 'Tier 2 · Manual', tier3: 'Tier 3 · Mock' }
const TIER_CLS = { tier1: 'tier-1', tier2: 'tier-2', tier3: 'tier-3' }

const CHECK_LABELS = {
  gst_status: 'GST Registration', pan_validity: 'PAN Validity', mca_status: 'MCA21 Status',
  epfo_registration: 'EPFO Registration', udyam_msme: 'Udyam / MSME',
  bis_license: 'BIS License', startup_india_dpiit: 'Startup India / DPIIT',
  nsic_registration: 'NSIC', blacklist: 'Blacklist / Debarment',
}

export default function BidderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [running, setRunning] = useState(false)
  const [toast, setToast] = useState('')
  const [overrideModal, setOverrideModal] = useState(null)
  const [overrideForm, setOverrideForm] = useState({ new_status: 'pass', reason: '' })
  const [tier2Modal, setTier2Modal] = useState(null)
  const [tier2Form, setTier2Form] = useState({ result: 'verified', notes: '' })

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3500) }

  const load = () => api.get(`/compliance/${id}`).then(r => setData(r.data))
  useEffect(() => { load() }, [id])

  const runCompliance = async () => {
    setRunning(true)
    try { await api.post(`/compliance/run/${id}`); await load(); showToast('✅ Compliance run complete!') }
    catch { showToast('❌ Error running compliance') }
    finally { setRunning(false) }
  }

  const submitOverride = async () => {
    await api.post(`/compliance/override/${id}`, { check_name: overrideModal.check_name, ...overrideForm })
    setOverrideModal(null); setOverrideForm({ new_status: 'pass', reason: '' })
    await load(); showToast('✅ Override applied and logged in audit trail.')
  }

  const submitTier2 = async () => {
    await api.post(`/compliance/tier2-verify/${id}`, { check_name: tier2Modal.check_name, ...tier2Form })
    setTier2Modal(null); setTier2Form({ result: 'verified', notes: '' })
    await load(); showToast('✅ Manual verification recorded!')
  }

  if (!data) return <div className="loading-center"><div className="spinner" /></div>

  const score = data.compliance_score
  const scoreClass = score >= 90 ? 'score-bar-low' : score >= 70 ? 'score-bar-medium' : score >= 40 ? 'score-bar-high' : 'score-bar-critical'

  return (
    <>
      <div className="page-header">
        <p className="text-sm text-muted" style={{ cursor: 'pointer', marginBottom: 4 }} onClick={() => navigate(-1)}>← Back</p>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">{data.company_name}</h1>
            <p className="page-subtitle">Bidder Compliance Detail View</p>
          </div>
          <div className="flex gap-3">
            <a
              href={`/api/audit/bidder/${id}/export-pdf`}
              target="_blank" rel="noreferrer"
              className="btn btn-secondary"
              title="Download PDF Audit Report"
            >
              <Download size={14} /> Export PDF
            </a>
            <button id="run-compliance-btn" className="btn btn-primary" onClick={runCompliance} disabled={running}>
              {running ? <><RefreshCw size={14} style={{ animation: 'spin 0.7s linear infinite' }} /> Verifying...</> : <><Play size={14} /> Run Verification</>}
            </button>
          </div>
        </div>
      </div>

      <div className="page-content">
        {/* Score card */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Compliance Score</span>
              {data.risk_level && <span className={`risk-badge ${RISK_CLASS[data.risk_level]}`}>{data.risk_level} Risk</span>}
            </div>
            {score != null ? (
              <>
                <div style={{ fontSize: 52, fontWeight: 900, letterSpacing: -2, lineHeight: 1 }}>{score}<span style={{ fontSize: 20, color: 'var(--text-muted)' }}>/100</span></div>
                <div className="score-bar-track" style={{ marginTop: 12, height: 8 }}>
                  <div className={`score-bar-fill ${scoreClass}`} style={{ width: `${score}%` }} />
                </div>
              </>
            ) : (
              <div className="text-muted" style={{ padding: '16px 0' }}>Run verification to see score</div>
            )}
          </div>

          <div className="card">
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>Check Summary</div>
            {data.checks.length === 0 ? (
              <p className="text-muted text-sm">No checks run yet. Click "Run Verification".</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {['pass', 'fail', 'manual_review', 'not_applicable'].map(s => {
                  const count = data.checks.filter(c => c.status === s).length
                  return count > 0 ? (
                    <div key={s} className="flex items-center justify-between">
                      <span className={`check-badge ${STATUS_INFO[s]?.cls}`}>{STATUS_INFO[s]?.label}</span>
                      <span style={{ fontWeight: 700 }}>{count}</span>
                    </div>
                  ) : null
                })}
              </div>
            )}
          </div>
        </div>

        {/* Compliance checks grid */}
        {data.checks.length > 0 && (
          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ fontWeight: 700, marginBottom: 16 }}>Compliance Checks</h3>
            <div className="compliance-grid">
              {data.checks.map(c => (
                <div key={c.id} className="check-card">
                  <div className="check-card-header">
                    <span className="check-card-name">{CHECK_LABELS[c.check_name] || c.check_name}</span>
                    <span className={`check-badge ${STATUS_INFO[c.status]?.cls}`}>{STATUS_INFO[c.status]?.label}</span>
                  </div>
                  <div className="check-card-detail">{c.detail || '—'}</div>
                  <div className="flex items-center justify-between mt-2">
                    <span className={`tier-badge ${TIER_CLS[c.check_tier]}`}>{TIER_LABEL[c.check_tier]}</span>
                    <div className="flex gap-2">
                      {c.check_tier === 'tier2' && c.tier2_portal_url && (
                        <button className="btn btn-secondary btn-xs" onClick={() => setTier2Modal(c)}>
                          <ExternalLink size={10} /> Verify ↗
                        </button>
                      )}
                      <button className="btn btn-secondary btn-xs" onClick={() => setOverrideModal(c)} title="Officer Override">
                        <Edit2 size={10} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Recommendation */}
        {data.recommendation && (
          <div className="recommendation-box">
            <h4>🤖 AI Recommendation (Python Template Engine)</h4>
            <div style={{ whiteSpace: 'pre-wrap', fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
              {data.recommendation}
            </div>
          </div>
        )}
      </div>

      {/* Tier 2 Manual Verify Modal */}
      {tier2Modal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div className="card" style={{ width: '100%', maxWidth: 480 }}>
            <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Tier 2 Manual Verification</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}><strong>{CHECK_LABELS[tier2Modal.check_name]}</strong></p>
            <div style={{ background: 'var(--warning-bg)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 8, padding: '12px 14px', marginBottom: 16 }}>
              <p style={{ fontSize: 12.5 }}>1. Click the button below to open the official government portal</p>
              <p style={{ fontSize: 12.5 }}>2. Complete the verification manually</p>
              <p style={{ fontSize: 12.5 }}>3. Record your result here</p>
            </div>
            <a href={tier2Modal.tier2_portal_url} target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
              <ExternalLink size={14} /> Open Official Portal ↗
            </a>
            <div className="form-group">
              <label>Verification Result</label>
              <select className="select" value={tier2Form.result} onChange={e => setTier2Form({ ...tier2Form, result: e.target.value })}>
                <option value="verified">✅ Verified — Registration confirmed</option>
                <option value="failed">❌ Failed — Not found / expired</option>
                <option value="discrepancy">⚠️ Discrepancy — Details don't match</option>
              </select>
            </div>
            <div className="form-group">
              <label>Officer Notes (optional)</label>
              <textarea className="textarea" value={tier2Form.notes} onChange={e => setTier2Form({ ...tier2Form, notes: e.target.value })} placeholder="Additional observations..." />
            </div>
            <div className="flex gap-3">
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setTier2Modal(null)}>Cancel</button>
              <button id="tier2-submit-btn" className="btn btn-primary" style={{ flex: 1 }} onClick={submitTier2}>Record Result</button>
            </div>
          </div>
        </div>
      )}

      {/* Override Modal */}
      {overrideModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div className="card" style={{ width: '100%', maxWidth: 440 }}>
            <div className="flex items-center gap-2 mb-4">
              <Shield size={16} color="var(--warning)" />
              <h3 style={{ fontWeight: 700 }}>Officer Override</h3>
            </div>
            <div style={{ background: 'var(--danger-bg)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 16 }}>
              <p style={{ fontSize: 12.5, color: 'var(--danger)' }}>⚠️ This override is logged in the immutable audit trail with your officer ID and timestamp.</p>
            </div>
            <p style={{ fontSize: 13, marginBottom: 12 }}>
              Overriding: <strong>{CHECK_LABELS[overrideModal.check_name] || overrideModal.check_name}</strong><br />
              Current status: <span className={`check-badge ${STATUS_INFO[overrideModal.status]?.cls}`}>{STATUS_INFO[overrideModal.status]?.label}</span>
            </p>
            <div className="form-group">
              <label>New Status</label>
              <select className="select" value={overrideForm.new_status} onChange={e => setOverrideForm({ ...overrideForm, new_status: e.target.value })}>
                <option value="pass">✅ Pass</option>
                <option value="fail">❌ Fail</option>
              </select>
            </div>
            <div className="form-group">
              <label>Mandatory Reason *</label>
              <textarea id="override-reason" className="textarea" required value={overrideForm.reason} onChange={e => setOverrideForm({ ...overrideForm, reason: e.target.value })} placeholder="Provide written justification for this override..." />
            </div>
            <div className="flex gap-3">
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setOverrideModal(null)}>Cancel</button>
              <button id="override-submit-btn" className="btn btn-danger" style={{ flex: 1 }} onClick={submitOverride} disabled={!overrideForm.reason.trim()}>Apply Override</button>
            </div>
          </div>
        </div>
      )}

      {toast && <div className="toast">{toast}</div>}
    </>
  )
}
