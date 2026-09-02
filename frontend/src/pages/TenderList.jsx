import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { Plus, FileText, ChevronRight, X } from 'lucide-react'

const DEFAULT_TOGGLES = {
  epfo_required: true,
  msme_exemption: false,
  bis_required: false,
  make_in_india: true,
  startup_india_eligible: false,
}

export default function TenderList() {
  const [tenders, setTenders] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ tender_number: '', title: '', department: '', description: '', rule_toggles: DEFAULT_TOGGLES })
  const [saving, setSaving] = useState(false)
  const navigate = useNavigate()

  const load = () => api.get('/tenders/').then(r => setTenders(r.data))
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      await api.post('/tenders/', form)
      setShowForm(false)
      setForm({ tender_number: '', title: '', department: '', description: '', rule_toggles: DEFAULT_TOGGLES })
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Error creating tender')
    } finally { setSaving(false) }
  }

  return (
    <>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Tenders</h1>
            <p className="page-subtitle">Manage procurement tenders and bidder compliance</p>
          </div>
          <button id="create-tender-btn" className="btn btn-primary" onClick={() => setShowForm(true)}>
            <Plus size={15} /> New Tender
          </button>
        </div>
      </div>

      <div className="page-content">
        {/* Create Form Modal */}
        {showForm && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
            <div className="card" style={{ width: '100%', maxWidth: 560, maxHeight: '90vh', overflow: 'auto' }}>
              <div className="flex items-center justify-between mb-4">
                <h3 style={{ fontSize: 16, fontWeight: 700 }}>Create New Tender</h3>
                <button onClick={() => setShowForm(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}><X size={18} /></button>
              </div>
              <form onSubmit={handleCreate}>
                <div className="form-group">
                  <label>Tender Number *</label>
                  <input id="tender-number" className="input" value={form.tender_number} onChange={e => setForm({ ...form, tender_number: e.target.value })} placeholder="CPCL/2026/PE/001" required />
                </div>
                <div className="form-group">
                  <label>Title *</label>
                  <input id="tender-title" className="input" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Supply of Petroleum Equipment" required />
                </div>
                <div className="form-group">
                  <label>Department</label>
                  <input className="input" value={form.department} onChange={e => setForm({ ...form, department: e.target.value })} placeholder="CPCL — Ministry of Petroleum" />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea className="textarea" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Tender scope and requirements..." />
                </div>
                <div className="form-group">
                  <label style={{ marginBottom: 10 }}>Rule Toggles</label>
                  {Object.entries(form.rule_toggles).map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between" style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                      <span style={{ fontSize: 13, textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</span>
                      <button type="button" onClick={() => setForm({ ...form, rule_toggles: { ...form.rule_toggles, [key]: !val } })}
                        style={{ width: 40, height: 22, borderRadius: 11, background: val ? 'var(--accent)' : 'var(--border)', border: 'none', cursor: 'pointer', transition: 'background 0.2s', position: 'relative' }}>
                        <span style={{ position: 'absolute', width: 16, height: 16, background: 'white', borderRadius: '50%', top: 3, left: val ? 20 : 4, transition: 'left 0.2s' }} />
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex gap-3">
                  <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowForm(false)}>Cancel</button>
                  <button id="save-tender-btn" type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={saving}>{saving ? 'Creating...' : 'Create Tender'}</button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="card">
          {tenders.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 48 }}>
              <FileText size={40} style={{ color: 'var(--text-muted)', margin: '0 auto 12px', display: 'block' }} />
              <p className="text-muted">No tenders yet. Create your first tender.</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Tender No.</th><th>Title</th><th>Department</th><th>Status</th><th>Created</th><th></th></tr></thead>
                <tbody>
                  {tenders.map(t => (
                    <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/tenders/${t.id}`)}>
                      <td className="font-mono">{t.tender_number}</td>
                      <td style={{ fontWeight: 500 }}>{t.title}</td>
                      <td className="text-muted text-sm">{t.department || '—'}</td>
                      <td><span className={`check-badge ${t.is_active ? 'check-pass' : 'check-na'}`}>{t.is_active ? 'Active' : 'Inactive'}</span></td>
                      <td className="text-muted text-sm">{new Date(t.created_at).toLocaleDateString('en-IN')}</td>
                      <td><ChevronRight size={14} color="var(--text-muted)" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
