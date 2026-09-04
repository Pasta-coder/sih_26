import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Play, RefreshCw, ExternalLink, Edit2, Shield, Download, ScrollText, X } from 'lucide-react'

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

const DOC_TYPES = [
  ['pan_card', 'PAN Card'],
  ['gst_certificate', 'GST Certificate'],
  ['udyam_certificate', 'Udyam Certificate'],
  ['epfo_certificate', 'EPFO Certificate'],
  ['itr_v_acknowledgment', 'ITR-V Acknowledgment'],
  ['oem_authorization_letter', 'OEM Authorization Letter'],
]

const CHECK_LABELS = {
  gst_status: 'GST Registration', pan_validity: 'PAN Validity', mca_status: 'MCA21 Status',
  epfo_registration: 'EPFO Registration', udyam_msme: 'Udyam / MSME',
  make_in_india: 'Make in India Local Content',
  bis_license: 'BIS License', startup_india_dpiit: 'Startup India / DPIIT',
  nsic_registration: 'NSIC', blacklist: 'Blacklist / Debarment',
}

export default function BidderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const [data, setData] = useState(null)
  const [running, setRunning] = useState(false)
  const [toast, setToast] = useState('')
  const [overrideModal, setOverrideModal] = useState(null)
  const [overrideForm, setOverrideForm] = useState({ new_status: 'pass', reason: '' })
  const [tier2Modal, setTier2Modal] = useState(null)
  const [tier2Form, setTier2Form] = useState({ result: 'verified', notes: '' })
  // F1: per-bidder audit trail (officer-accessible) modal
  const [auditModal, setAuditModal] = useState(null)
  const [auditError, setAuditError] = useState('')
  // M3: document upload + advisory cross-check
  const [docReport, setDocReport] = useState(null)
  const [docType, setDocType] = useState('pan_card')
  const [docFile, setDocFile] = useState(null)
  const [uploading, setUploading] = useState(false)

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3500) }

  const load = () => api.get(`/compliance/${id}`).then(r => setData(r.data))
  const loadDocs = () => api.get(`/documents/consistency/${id}`).then(r => setDocReport(r.data)).catch(() => {})
  useEffect(() => { load(); loadDocs() }, [id])

  const uploadDoc = async (e) => {
    e.preventDefault()
    if (!docFile) return
    const fd = new FormData()
    fd.append('doc_type', docType)
    fd.append('file', docFile)
    setUploading(true)
    try {
      await api.post(`/documents/upload/${id}`, fd)
      setDocFile(null)
      e.target.reset?.()
      await loadDocs()
      showToast('✅ Document uploaded and cross-checked')
    } catch (err) {
      showToast(`❌ ${err.response?.data?.detail || 'Upload failed'}`)
    } finally {
      setUploading(false)
    }
  }

  const openAuditTrail = async () => {
    setAuditModal({ loading: true, entries: [] })
    setAuditError('')
    try {
      const r = await api.get(`/audit/bidder/${id}`)
      setAuditModal({ loading: false, entries: r.data })
    } catch {
      setAuditError('Could not load the audit trail for this bidder.')
      setAuditModal({ loading: false, entries: [] })
    }
  }

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
  // E5: pending manual checks are excluded from scoring — say so next to the score.
  const pendingCount = data.checks.filter(c => c.status === 'manual_review').length

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
            <button className="btn btn-secondary" onClick={openAuditTrail} title="Immutable per-bidder audit trail">
              <ScrollText size={14} /> View Audit Trail
            </button>
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
                {pendingCount > 0 && (
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 10 }}>
                    ⏳ Score excludes {pendingCount} pending manual check{pendingCount > 1 ? 's' : ''} — updates after officer verification
                  </p>
                )}
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
              {data.checks.map(c => {
                // S2: the blacklist verdict is a hard auto-disqualifier — only admins may override it.
                const isBlacklist = c.check_name === 'blacklist'
                const overrideLocked = isBlacklist && !isAdmin
                return (
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
                        <button
                          className="btn btn-secondary btn-xs"
                          disabled={overrideLocked}
                          onClick={() => setOverrideModal(c)}
                          title={overrideLocked
                            ? 'Blacklist verdicts are a hard auto-disqualifier — Admin override only'
                            : 'Officer Override'}
                          style={overrideLocked ? { opacity: 0.45, cursor: 'not-allowed' } : undefined}
                        >
                          <Edit2 size={10} />
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Documents & cross-check (M3) */}
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ fontWeight: 700, marginBottom: 4 }}>📄 Documents & Cross-Check</h3>
          <p className="text-sm text-muted" style={{ marginBottom: 16 }}>
            Upload a compliance document; OCR-extracted PAN/GSTIN/Udyam/EPFO codes and names are compared against the bidder record. This panel is advisory only — registry checks remain authoritative.
          </p>
          <form onSubmit={uploadDoc} className="flex gap-2" style={{ flexWrap: 'wrap' }}>
            <select className="select" style={{ maxWidth: 220 }} value={docType} onChange={e => setDocType(e.target.value)}>
              {DOC_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
            <input type="file" accept="image/*,.pdf" className="input" style={{ flex: 1, minWidth: 180, padding: 7 }} onChange={e => setDocFile(e.target.files?.[0] || null)} />
            <button className="btn btn-primary btn-sm" type="submit" disabled={uploading || !docFile}>
              {uploading ? 'Uploading…' : 'Upload & Extract'}
            </button>
          </form>

          <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {(!docReport || docReport.documents.length === 0) ? (
              <p className="text-sm text-muted">No documents uploaded yet.</p>
            ) : docReport.documents.map(d => (
              <div key={d.document_id} style={{ background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 8, padding: '12px 14px' }}>
                <div className="flex items-center justify-between mb-1">
                  <span style={{ fontSize: 12.5, fontWeight: 600 }}>{d.filename}</span>
                  <span className="tier-badge tier-2">{d.doc_type.replace(/_/g, ' ')}</span>
                </div>
                <div className="flex" style={{ flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
                  {d.checks.length === 0 && <span className="text-sm text-muted">No record fields to cross-check for this document type.</span>}
                  {d.checks.map((c, i) => (
                    <span key={i} className={`check-badge ${c.status === 'matched' ? 'check-pass' : c.status === 'mismatch' ? 'check-fail' : 'check-na'}`} title={`record: ${c.record ?? '—'}`}>
                      {c.status === 'matched' ? '✓' : c.status === 'mismatch' ? '✗' : '·'} {c.field}: {c.extracted ?? 'no OCR data'}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Recommendation */}
        {data.recommendation && (
          <div className="recommendation-box">
            <h4>🤖 AI Recommendation (Python Template Engine)</h4>
            {/* F4: react-markdown renders the stored markdown (escaped by default, so no XSS). */}
            <div className="recommendation-markdown">
              <ReactMarkdown>{data.recommendation}</ReactMarkdown>
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
              <p style={{ fontSize: 11.5, marginTop: 6, color: 'var(--text-muted)' }}>
                ⚠️ &quot;Discrepancy&quot; is recorded as a Fail — clear it only via Override with written justification.
              </p>
            </div>
            <a href={tier2Modal.tier2_portal_url} target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
              <ExternalLink size={14} /> Open Official Portal ↗
            </a>
            <div className="form-group">
              <label>Verification Result</label>
              <select className="select" value={tier2Form.result} onChange={e => setTier2Form({ ...tier2Form, result: e.target.value })}>
                <option value="verified">✅ Verified — Registration confirmed</option>
                <option value="failed">❌ Failed — Not found / expired</option>
                {/* E4: discrepancy is an officer-recorded Fail, cleared only via Override */}
                <option value="discrepancy">⚠️ Discrepancy — recorded as Fail (use Override to clear)</option>
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

      {/* Audit Trail Modal (F1) */}
      {auditModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div className="card" style={{ width: '100%', maxWidth: 640, maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <ScrollText size={16} color="var(--accent)" />
                <h3 style={{ fontWeight: 700 }}>Audit Trail — {data.company_name}</h3>
              </div>
              <button className="btn btn-secondary btn-xs" onClick={() => { setAuditModal(null); setAuditError('') }}>
                <X size={12} /> Close
              </button>
            </div>
            <div style={{ overflow: 'auto', flex: 1 }}>
              {auditError ? (
                <p style={{ color: 'var(--danger)', fontSize: 13, padding: 12 }}>{auditError}</p>
              ) : auditModal.loading ? (
                <div className="loading-center" style={{ padding: 32 }}><div className="spinner" /></div>
              ) : auditModal.entries.length === 0 ? (
                <p className="text-muted" style={{ padding: 24 }}>No audit events recorded for this bidder yet.</p>
              ) : (
                auditModal.entries.map(e => (
                  <div key={e.id} className="audit-entry">
                    <div className="audit-dot" style={{ background: 'var(--accent)' }} />
                    <div style={{ flex: 1 }}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="audit-time">{new Date(e.timestamp).toLocaleString('en-IN')}</span>
                        <span style={{ fontSize: 10, background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 4, padding: '1px 6px', color: 'var(--text-muted)' }}>
                          {e.event_type}
                        </span>
                      </div>
                      <div className="audit-desc">{e.description}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {toast && <div className="toast">{toast}</div>}
    </>
  )
}
