import { useState, useEffect } from 'react'
import api from '../api/client'
import { ScrollText } from 'lucide-react'

const EVENT_COLORS = {
  tier1_query: '#10b981',
  tier2_manual_verify: '#f59e0b',
  tier3_mock_query: '#6366f1',
  document_upload: '#8b5cf6',
  document_extraction: '#a855f7',  // F5
  rules_verdict: '#3b82f6',
  recommendation_generated: '#ec4899',
  officer_override: '#ef4444',
  compliance_run_started: '#6366f1',
  compliance_run_completed: '#10b981',
  bidder_created: '#94a3b8',
}

export default function AuditLog() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')

  // F1: surface load failures instead of silently rendering an empty state.
  useEffect(() => {
    api.get('/audit/all')
      .then(r => setEntries(r.data))
      .catch(() => setError('Could not load the audit log. This view is restricted to administrators.'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all' ? entries : entries.filter(e => e.event_type === filter)
  const types = [...new Set(entries.map(e => e.event_type))]

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Audit Log</h1>
        <p className="page-subtitle">Immutable record of all system events — PRD §12</p>
      </div>

      <div className="page-content">
        {/* Filter */}
        <div className="flex gap-2 mb-4" style={{ flexWrap: 'wrap' }}>
          <button className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('all')}>All</button>
          {types.map(t => (
            <button key={t} className={`btn btn-sm ${filter === t ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter(t)}>
              {t.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        <div className="card">
          {loading ? (
            <div className="loading-center"><div className="spinner" /></div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--danger)' }}>
              <ScrollText size={40} style={{ color: 'var(--danger)', margin: '0 auto 12px', display: 'block', opacity: 0.6 }} />
              <p>{error}</p>
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <ScrollText size={40} style={{ color: 'var(--text-muted)', margin: '0 auto 12px', display: 'block' }} />
              <p className="text-muted">No audit entries yet. Run a compliance check first.</p>
            </div>
          ) : (
            filtered.map(e => (
              <div key={e.id} className="audit-entry">
                <div className="audit-dot" style={{ background: EVENT_COLORS[e.event_type] || 'var(--accent)' }} />
                <div style={{ flex: 1 }}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="audit-time">{new Date(e.timestamp).toLocaleString('en-IN')}</span>
                    <span style={{ fontSize: 10, background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 4, padding: '1px 6px', color: 'var(--text-muted)' }}>
                      {e.event_type}
                    </span>
                    {e.bidder_id && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>bidder #{e.bidder_id}</span>}
                  </div>
                  <div className="audit-desc">{e.description}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  )
}
