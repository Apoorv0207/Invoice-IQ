import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, RefreshCw, Loader, Brain, FileCheck } from 'lucide-react'
import { useInvoice } from '../hooks/useInvoices'
import { getExplanations } from '../utils/api'
import StatusBadge from '../components/StatusBadge'
import ReviewPanel from '../components/ReviewPanel'
import ExportButton from '../components/ExportButton'
import POMatchPanel from '../components/POMatchPanel'
import ExplainabilityPanel from '../components/ExplainabilityPanel'

const DETAIL_TABS = ['Review', 'PO Match', 'AI Reasoning']

function Field({ label, value, mono = false }) {
  return (
    <div>
      <p className="text-xs text-slate-500 mb-0.5">{label}</p>
      <p className={`text-sm ${mono ? 'font-mono' : ''} ${value ? 'text-slate-200' : 'text-slate-600 italic'}`}>
        {value || 'not found'}
      </p>
    </div>
  )
}

function LineItemsTable({ items }) {
  if (!items?.length) return <p className="text-slate-600 text-sm">No line items</p>
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800">
            {['Description','Qty','Rate','Total','GL Code'].map(h => (
              <th key={h} className={`py-2 px-3 text-slate-500 font-medium ${h === 'Description' ? 'text-left' : 'text-right'}`}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50">
          {items.map((item, i) => (
            <tr key={i}>
              <td className="py-2 px-3 text-slate-300">{item.description}</td>
              <td className="py-2 px-3 text-right font-mono text-slate-400">{item.quantity}</td>
              <td className="py-2 px-3 text-right font-mono text-slate-400">₹{Number(item.unit_price || 0).toLocaleString('en-IN')}</td>
              <td className="py-2 px-3 text-right font-mono text-slate-200">₹{Number(item.total || 0).toLocaleString('en-IN')}</td>
              <td className="py-2 px-3">
                {item.gl_code
                  ? <span className="text-xs font-mono"><span className="text-brand-400">{item.gl_code}</span><span className="text-slate-600 ml-1">· {item.gl_description}</span></span>
                  : <span className="text-slate-600">—</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function InvoiceDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { invoice, loading, refetch } = useInvoice(id)
  const [rightTab, setRightTab] = useState('Review')
  const [explanations, setExplanations] = useState(null)
  const [expLoading, setExpLoading] = useState(false)

  const loadExplanations = async () => {
    if (explanations) return
    setExpLoading(true)
    try {
      const data = await getExplanations(id)
      setExplanations(data.explanations || [])
    } finally {
      setExpLoading(false)
    }
  }

  const handleTabClick = (tab) => {
    setRightTab(tab)
    if (tab === 'AI Reasoning') loadExplanations()
  }

  if (loading && !invoice) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loader size={24} className="animate-spin text-brand-400" />
      </div>
    )
  }

  if (!invoice) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">Invoice not found.</div>
  )

  const data = invoice.extracted_data || {}
  const isProcessing = invoice.status === 'processing'

  return (
    <div className="min-h-screen bg-slate-950">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors text-sm">
          <ArrowLeft size={15} /> Back
        </button>
        <div className="flex items-center gap-3">
          <StatusBadge status={invoice.status} />
          {!isProcessing && <ExportButton invoiceId={invoice.id} />}
          <button onClick={refetch} className="btn-ghost p-2">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-slate-100">{invoice.file_name}</h1>
          <div className="flex items-center gap-4 mt-1">
            <p className="text-slate-500 text-sm">
              {new Date(invoice.created_at).toLocaleString('en-IN')}
            </p>
            {invoice.confidence_score != null && (
              <span className="text-sm font-mono text-slate-400">Confidence: {invoice.confidence_score}%</span>
            )}
            {invoice.processing_time_ms != null && (
              <span className="text-xs text-slate-600">{(invoice.processing_time_ms/1000).toFixed(1)}s processing</span>
            )}
          </div>
        </div>

        {isProcessing ? (
          <div className="card text-center py-16">
            <Loader size={32} className="animate-spin text-brand-400 mx-auto mb-4" />
            <p className="text-slate-300 font-medium">Running 6-node AI pipeline...</p>
            <p className="text-slate-500 text-sm mt-1">Extract → Math → Duplicate → PO Match → GL → Explain</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left */}
            <div className="lg:col-span-2 space-y-5">
              <div className="card">
                <h2 className="font-medium text-slate-300 mb-4 text-sm">Invoice Details</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <Field label="Vendor Name" value={data.vendor_name} />
                  <Field label="Invoice Number" value={data.invoice_number} mono />
                  <Field label="PO Number" value={data.po_number} mono />
                  <Field label="Invoice Date" value={data.invoice_date} mono />
                  <Field label="Due Date" value={data.due_date} mono />
                  <Field label="Payment Terms" value={data.payment_terms} />
                </div>
              </div>

              <div className="card">
                <h2 className="font-medium text-slate-300 mb-4 text-sm">Financials</h2>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-xs text-slate-500 mb-1">Subtotal</p>
                    <p className="text-lg font-mono font-semibold text-slate-200">
                      {data.subtotal != null ? `₹${Number(data.subtotal).toLocaleString('en-IN')}` : '—'}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-slate-500 mb-1">Tax</p>
                    <p className="text-lg font-mono font-semibold text-slate-200">
                      {data.tax_amount != null ? `₹${Number(data.tax_amount).toLocaleString('en-IN')}` : '—'}
                    </p>
                  </div>
                  <div className="text-center border-l border-slate-700">
                    <p className="text-xs text-slate-500 mb-1">Total</p>
                    <p className="text-2xl font-mono font-bold text-slate-100">
                      {data.total_amount != null ? `₹${Number(data.total_amount).toLocaleString('en-IN')}` : '—'}
                    </p>
                  </div>
                </div>
                {invoice.validation && (
                  <div className={`mt-4 text-xs px-3 py-2 rounded-lg ${invoice.validation.math_valid ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                    {invoice.validation.math_valid
                      ? '✓ Math validation passed'
                      : `✗ Math mismatch — ₹${invoice.validation.math_discrepancy}`}
                  </div>
                )}
              </div>

              <div className="card">
                <h2 className="font-medium text-slate-300 mb-4 text-sm">
                  Line Items <span className="text-slate-600 font-normal">({data.line_items?.length || 0})</span>
                </h2>
                <LineItemsTable items={data.line_items} />
              </div>
            </div>

            {/* Right panel with tabs */}
            <div className="card h-fit">
              <div className="flex gap-1 mb-4 -mt-1">
                {DETAIL_TABS.map(tab => (
                  <button
                    key={tab}
                    onClick={() => handleTabClick(tab)}
                    className={`text-xs px-2.5 py-1 rounded-lg transition-colors font-medium flex-1 ${
                      rightTab === tab
                        ? 'bg-brand-600 text-white'
                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                  >
                    {tab === 'AI Reasoning' ? '🧠' : tab === 'PO Match' ? '📋' : '✏️'} {tab}
                  </button>
                ))}
              </div>

              {rightTab === 'Review' && (
                <ReviewPanel invoice={invoice} onReviewed={refetch} />
              )}
              {rightTab === 'PO Match' && (
                <POMatchPanel poMatch={invoice.po_match} invoiceData={data} />
              )}
              {rightTab === 'AI Reasoning' && (
                <ExplainabilityPanel
                  explanations={explanations || invoice.explainability || []}
                  loading={expLoading}
                />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
