import { useState } from 'react'
import { FileText, Download, BarChart2, Package } from 'lucide-react'
import UploadZone from '../components/UploadZone'
import InvoiceTable from '../components/InvoiceTable'
import AnalyticsDashboard from '../components/AnalyticsDashboard'
import { useInvoices } from '../hooks/useInvoices'
import { exportBatchCsv, uploadPO } from '../utils/api'
import { Zap, AlertTriangle, CheckCircle } from 'lucide-react'

function StatCard({ label, value, icon: Icon, color }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-2.5 rounded-lg ${color}`}><Icon size={18} /></div>
      <div>
        <p className="text-2xl font-bold text-slate-100">{value ?? 0}</p>
        <p className="text-xs text-slate-500">{label}</p>
      </div>
    </div>
  )
}

const FILTERS = [
  { value: null,               label: 'All' },
  { value: 'auto_approved',    label: 'Auto Approved' },
  { value: 'flagged',          label: 'Flagged' },
  { value: 'review_required',  label: 'Needs Review' },
  { value: 'approved',         label: 'Approved' },
  { value: 'processing',       label: 'Processing' },
]

const TABS = ['Invoices', 'Analytics', 'Purchase Orders']

export default function Dashboard() {
  const [statusFilter, setStatusFilter] = useState(null)
  const [activeTab, setActiveTab] = useState('Invoices')
  const [poUploading, setPOUploading] = useState(false)
  const [poMessage, setPOMessage] = useState(null)
  const { invoices, stats, loading, refetch } = useInvoices(statusFilter)

  const handlePOUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setPOUploading(true)
    setPOMessage(null)
    try {
      const result = await uploadPO(file)
      setPOMessage({ type: 'success', text: `PO uploaded: ${result.po_number || 'extracted'} for ${result.vendor_name}` })
    } catch (err) {
      setPOMessage({ type: 'error', text: `Upload failed: ${err.message}` })
    } finally {
      setPOUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center">
            <FileText size={14} className="text-white" />
          </div>
          <span className="font-semibold text-slate-100 text-lg tracking-tight">InvoiceIQ</span>
          <span className="text-xs text-slate-600 ml-1">v2</span>
        </div>
        <div className="flex items-center gap-2">
          <label className={`btn-ghost flex items-center gap-1.5 text-xs cursor-pointer ${poUploading ? 'opacity-50 pointer-events-none' : ''}`}>
            <Package size={13} />
            {poUploading ? 'Uploading PO...' : 'Upload PO'}
            <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png" onChange={handlePOUpload} />
          </label>
          <button onClick={() => exportBatchCsv('approved')} className="btn-ghost flex items-center gap-1.5 text-xs">
            <Download size={13} /> Export Approved
          </button>
        </div>
      </header>

      {poMessage && (
        <div className={`mx-6 mt-3 text-sm px-3 py-2 rounded-lg ${
          poMessage.type === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
        }`}>
          {poMessage.text}
        </div>
      )}

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Invoices" value={stats.total} icon={FileText} color="bg-slate-800 text-slate-400" />
          <StatCard label="Auto Approved" value={stats.auto_approved} icon={Zap} color="bg-emerald-500/10 text-emerald-400" />
          <StatCard label="Need Attention" value={(stats.flagged || 0) + (stats.review_required || 0)} icon={AlertTriangle} color="bg-amber-500/10 text-amber-400" />
          <StatCard label="Human Approved" value={stats.approved} icon={CheckCircle} color="bg-brand-500/10 text-brand-400" />
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-slate-800">
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab
                  ? 'border-brand-500 text-brand-400'
                  : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === 'Invoices' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="card">
              <h2 className="font-semibold text-slate-200 mb-4 text-sm uppercase tracking-wider">Upload Invoices</h2>
              <UploadZone onUploadComplete={refetch} />
            </div>
            <div className="lg:col-span-2 card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-slate-200 text-sm uppercase tracking-wider">Invoices</h2>
                <div className="flex gap-1 flex-wrap">
                  {FILTERS.map(f => (
                    <button
                      key={String(f.value)}
                      onClick={() => setStatusFilter(f.value)}
                      className={`text-xs px-2.5 py-1 rounded-full transition-colors font-medium ${
                        statusFilter === f.value
                          ? 'bg-brand-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>
              {loading
                ? <div className="text-center py-12 text-slate-600 text-sm">Loading...</div>
                : <InvoiceTable invoices={invoices} />
              }
            </div>
          </div>
        )}

        {activeTab === 'Analytics' && <AnalyticsDashboard />}

        {activeTab === 'Purchase Orders' && (
          <div className="card">
            <h2 className="font-semibold text-slate-200 mb-2 text-sm">Purchase Orders</h2>
            <p className="text-slate-500 text-sm mb-4">
              Upload PO documents using the "Upload PO" button in the header.
              Uploaded POs are automatically matched against incoming invoices.
            </p>
            <div className="text-slate-600 text-sm text-center py-8">
              Use the Upload PO button → upload a PO PDF →
              then upload a matching invoice to see the PO matching in action.
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
