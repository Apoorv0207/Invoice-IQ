import { useState, useEffect } from 'react'
import {
  getAnalyticsSummary, getVendorAnalytics,
  getTrend, getGLDistribution, getPOStats
} from '../utils/api'
import {
  FileText, Zap, Eye, XCircle, Copy, TrendingUp,
  Clock, Award, BarChart2
} from 'lucide-react'

// Simple bar using divs — no chart library needed
function MiniBar({ value, max, color = 'bg-brand-500' }) {
  const pct = max > 0 ? (value / max) * 100 : 0
  return (
    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
      <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
    </div>
  )
}

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="card flex items-start gap-3">
      <div className={`p-2 rounded-lg shrink-0 ${color}`}>
        <Icon size={16} />
      </div>
      <div className="min-w-0">
        <p className="text-xl font-bold text-slate-100">{value ?? '—'}</p>
        <p className="text-xs text-slate-500 font-medium">{label}</p>
        {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

function TrendChart({ trend }) {
  if (!trend.length) return <p className="text-slate-600 text-sm text-center py-4">No data yet</p>
  const maxVal = Math.max(...trend.map(t => t.total), 1)
  return (
    <div className="space-y-2">
      {trend.slice(-7).map((t, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-xs text-slate-600 w-20 shrink-0 font-mono">
            {t.date.slice(5)}
          </span>
          <div className="flex-1">
            <MiniBar value={t.total} max={maxVal} color="bg-brand-500" />
          </div>
          <span className="text-xs text-slate-400 w-6 text-right">{t.total}</span>
          <span className="text-xs text-emerald-500 w-6 text-right">{t.auto_approved}</span>
        </div>
      ))}
      <div className="flex gap-4 pt-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <div className="w-2 h-2 rounded-full bg-brand-500" /> Total
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <div className="w-2 h-2 rounded-full bg-emerald-500" /> Auto-approved
        </div>
      </div>
    </div>
  )
}

export default function AnalyticsDashboard() {
  const [summary, setSummary] = useState(null)
  const [vendors, setVendors] = useState([])
  const [trend, setTrend] = useState([])
  const [glCodes, setGLCodes] = useState([])
  const [poStats, setPOStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getAnalyticsSummary(),
      getVendorAnalytics(),
      getTrend(14),
      getGLDistribution(),
      getPOStats()
    ]).then(([s, v, t, gl, po]) => {
      setSummary(s)
      setVendors(v.top_vendors || [])
      setTrend(t.trend || [])
      setGLCodes(gl.top_gl_codes || [])
      setPOStats(po)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="text-center py-12 text-slate-600 text-sm">
        Loading analytics...
      </div>
    )
  }

  const s = summary || {}

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard icon={FileText} label="Total Processed" value={s.total_processed}
          color="bg-slate-800 text-slate-400" />
        <StatCard icon={Zap} label="Auto-Approved" value={s.status_breakdown?.auto_approved}
          sub={`${s.auto_approve_rate_percent}% rate`}
          color="bg-emerald-500/10 text-emerald-400" />
        <StatCard icon={Eye} label="Manual Reviews" value={s.manual_review_count}
          color="bg-amber-500/10 text-amber-400" />
        <StatCard icon={XCircle} label="Duplicates Found" value={s.duplicates_detected}
          color="bg-red-500/10 text-red-400" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard icon={Award} label="Avg Confidence" value={`${s.avg_confidence_score}%`}
          color="bg-brand-500/10 text-brand-400" />
        <StatCard icon={Clock} label="Avg Process Time"
          value={s.avg_processing_time_ms ? `${(s.avg_processing_time_ms/1000).toFixed(1)}s` : '—'}
          color="bg-purple-500/10 text-purple-400" />
        <StatCard icon={FileText} label="Rejected" value={s.status_breakdown?.rejected}
          color="bg-slate-800 text-slate-400" />
        <StatCard icon={BarChart2} label="PO Match Rate"
          value={poStats ? `${poStats.po_match_rate_percent}%` : '—'}
          sub={poStats ? `${poStats.po_pass} passed` : ''}
          color="bg-cyan-500/10 text-cyan-400" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Trend chart */}
        <div className="card">
          <h3 className="text-sm font-medium text-slate-300 mb-4 flex items-center gap-2">
            <TrendingUp size={14} className="text-brand-400" />
            14-Day Processing Trend
          </h3>
          <TrendChart trend={trend} />
        </div>

        {/* Top vendors */}
        <div className="card">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Top Vendors</h3>
          <div className="space-y-3">
            {vendors.slice(0, 5).map((v, i) => (
              <div key={i}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-slate-300 truncate max-w-[160px]">{v.vendor_name}</span>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs text-slate-500">{v.invoice_count} inv</span>
                    <span className="text-xs text-emerald-400">{v.approval_accuracy_percent}%</span>
                  </div>
                </div>
                <MiniBar value={v.approval_accuracy_percent} max={100} color="bg-emerald-500" />
              </div>
            ))}
            {!vendors.length && (
              <p className="text-slate-600 text-sm text-center py-3">No vendor data yet</p>
            )}
          </div>
        </div>
      </div>

      {/* GL code distribution */}
      <div className="card">
        <h3 className="text-sm font-medium text-slate-300 mb-4">Top GL Codes Used</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {glCodes.slice(0, 8).map((gl, i) => {
            const maxCount = glCodes[0]?.usage_count || 1
            return (
              <div key={i} className="flex items-center gap-3">
                <span className="font-mono text-xs text-brand-400 w-12 shrink-0">{gl.gl_code}</span>
                <div className="flex-1">
                  <div className="flex justify-between mb-0.5">
                    <span className="text-xs text-slate-400 truncate">{gl.description}</span>
                    <span className="text-xs text-slate-600 ml-2 shrink-0">{gl.usage_count}</span>
                  </div>
                  <MiniBar value={gl.usage_count} max={maxCount} color="bg-brand-500" />
                </div>
              </div>
            )
          })}
          {!glCodes.length && (
            <p className="text-slate-600 text-sm col-span-2 text-center py-3">No GL code data yet</p>
          )}
        </div>
      </div>
    </div>
  )
}
