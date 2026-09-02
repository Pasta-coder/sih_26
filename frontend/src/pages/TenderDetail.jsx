import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import { Play, Upload, ChevronRight, AlertTriangle, CheckCircle, XCircle, Clock, RefreshCw, Plus } from 'lucide-react'

const RISK_CLASS = { Low: 'risk-low', Medium: 'risk-medium', High: 'risk-high', Critical: 'risk-critical' }
const SCORE_CLASS = (s) => s >= 90 ? 'score-bar-low' : s >= 70 ? 'score-bar-medium' : s >= 40 ? 'score-bar-high' : 'score-bar-critical'

export default function TenderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tender, setTender] = useState(null)
  const [bidders, setBidders] = useState([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [showAddBidder, setShowAddBidder] = useState(false)
  const [bidderForm, setBidderForm] = useState({ company_name: '', gstin: '', pan: '', cin: '', udyam_number: '', epfo_code: '', email: '' })
  const [toast, setToast] = useState('')

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3000) }

  const load = async () => {
    const [t, b] = await Promise.all([api.get(`/tenders/${id}`), api.get(`/tenders/${id}/bidders`)])
    setTender(t.data); setBidders(b.data); setLoading(false)
  }
  useEffect(() => { load() }, [id])

  const runAll = async () => {
    setRunning(true)
    try {
      await api.post(`/compliance/run-all/${id}`)
      await load()
      showToast('✅ Compliance run complete for all bidders!')
    } catch (e) { showToast('❌ Error running compliance') }
    finally { setRunning(false) }
  }

  const addBidder = async (e) => {
    e.preventDefault()
    await api.post(`/tenders/${id}/bidders`, bidderForm)
    setShowAddBidder(false)
    setBidderForm({ company_name: '', gstin: '', pan: '', cin: '', udyam_number: '', epfo_code: '', email: '' })
    await load()
    showToast('✅ Bidder added!')
  }

  const handleCsvUpload = async (e) => {
    const file = e.target.files[0]; if (!file) return
    const fd = new FormData(); fd.append('file', file)
    await api.post(`/tenders/${id}/bidders/upload-csv`, fd)
    await load(); showToast('✅ CSV imported!')
  }

  if (loading) return <div className="loading-center"><div className="spinner" /></div>

  const riskCounts = bidders.reduce((acc, b) => { if (b.risk_level) acc[b.risk_level] = (acc[b.risk_level] || 0) + 1; return acc }, {})

  return (
    <>
      <div className="page-header">
        <p className="text-sm text-muted" style={{ marginBottom: 4, cursor: 'pointer' }} onClick={() => navigate('/tenders')}>← Tenders</p>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">{tender.tender_number}</h1>
            <p className="page-subtitle">{tender.title}</p>
          </div>
          <div className="flex gap-3">
            <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
              <Upload size={14} /> Import CSV
              <input type="file" accept=".csv" style={{ display: 'none' }} onChange={handleCsvUpload} />
            </label>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowAddBidder(true)}><Plus size={14} /> Add Bidder</button>
            <button id="run-all-btn" className="btn btn-primary" onClick={runAll} disabled={running || bidders.length === 0}>
              {running ? <><RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> Running...</> : <><Play size={14} /> Run All Compliance</>}
            </button>
          </div>
        </div>
      </div>

      <div className="page-content">
        {/* Risk Summary */}
        {Object.keys(riskCounts).length > 0 && (
          <div className="stat-grid">
            {['Critical', 'High', 'Medium', 'Low'].map(r => riskCounts[r] ? (
              <div key={r} className="stat-card">
                <div className={`risk-badge ${RISK_CLASS[r]}`}>{r}</div>
                <div className="stat-value" style={{ marginLeft: 8 }}>{riskCounts[r]}</div>
              </div>
            ) : null)}
          </div>
        )}

        {/* Add Bidder Modal */}
        {showAddBidder && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
            <div className="card" style={{ width: '100%', maxWidth: 500, maxHeight: '90vh', overflow: 'auto' }}>
              <h3 style={{ fontWeight: 700, marginBottom: 20 }}>Add Bidder</h3>
              <form onSubmit={addBidder}>
                {[
                  ['company_name', 'Company Name *', 'Reliance Industries Ltd', true],
                  ['gstin', 'GSTIN', '27AAACR5055K1ZK'],
                  ['pan', 'PAN', 'AAACR5055K'],
                  ['cin', 'CIN', 'L17110MH1973PLC019786'],
                  ['udyam_number', 'Udyam Number', 'UDYAM-MH-23-0001234'],
                  ['epfo_code', 'EPFO Code', 'MHBAN0012345000'],
                  ['email', 'Email', 'vendor@company.com'],
                ].map(([field, lbl, ph, req]) => (
                  <div className="form-group" key={field}>
                    <label>{lbl}</label>
                    <input className="input" value={bidderForm[field]} onChange={e => setBidderForm({ ...bidderForm, [field]: e.target.value })} placeholder={ph} required={req} />
                  </div>
                ))}
                <div className="flex gap-3">
                  <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowAddBidder(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Add Bidder</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Bidders Table */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 style={{ fontWeight: 700 }}>Bidders — Ranked by Compliance Score</h3>
            <span className="text-sm text-muted">{bidders.length} bidder{bidders.length !== 1 ? 's' : ''}</span>
          </div>
          {bidders.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No bidders yet. Add bidders or import CSV.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>#</th><th>Company</th><th>GSTIN</th><th>Score</th><th>Risk</th><th>Status</th><th></th></tr></thead>
                <tbody>
                  {bidders.map((b, i) => (
                    <tr key={b.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/bidder/${b.id}`)}>
                      <td className="text-muted text-sm">{i + 1}</td>
                      <td style={{ fontWeight: 500 }}>{b.company_name}</td>
                      <td className="font-mono">{b.gstin || '—'}</td>
                      <td style={{ minWidth: 160 }}>
                        {b.compliance_score != null ? (
                          <div className="score-bar-wrap">
                            <div className="score-bar-track">
                              <div className={`score-bar-fill ${SCORE_CLASS(b.compliance_score)}`} style={{ width: `${b.compliance_score}%` }} />
                            </div>
                            <span style={{ fontSize: 12, fontWeight: 700, minWidth: 36 }}>{b.compliance_score}</span>
                          </div>
                        ) : <span className="text-muted text-sm">Not run</span>}
                      </td>
                      <td>{b.risk_level ? <span className={`risk-badge ${RISK_CLASS[b.risk_level]}`}>{b.risk_level}</span> : '—'}</td>
                      <td><span className={`check-badge ${b.status === 'completed' ? 'check-pass' : b.status === 'in_progress' ? 'check-pending' : 'check-na'}`}>{b.status}</span></td>
                      <td><ChevronRight size={14} color="var(--text-muted)" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {toast && <div className="toast">{toast}</div>}
    </>
  )
}
