import { useNavigate } from 'react-router-dom'
import { FileText, ChevronRight, AlertTriangle } from 'lucide-react'
import StatusBadge from './StatusBadge'

function ConfidenceBar({ score }) {
  if (score == null) return <span className="text-slate-600 text-xs">—</span>
  const color = score >= 95 ? 'bg-emerald-500' : score >= 75 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs text-slate-400 font-mono">{score}%</span>
    </div>
  )
}

export default function InvoiceTable({ invoices }) {
  const navigate = useNavigate()

  if (!invoices.length) {
    return (
      <div className="text-center py-16 text-slate-600">
        <FileText size={40} className="mx-auto mb-3 opacity-30" />
        <p>No invoices yet. Upload one to get started.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="text-left py-3 px-4 text-slate-500 font-medium">File</th>
            <th className="text-left py-3 px-4 text-slate-500 font-medium">Vendor</th>
            <th className="text-left py-3 px-4 text-slate-500 font-medium">Invoice #</th>
            <th className="text-right py-3 px-4 text-slate-500 font-medium">Amount</th>
            <th className="text-left py-3 px-4 text-slate-500 font-medium">Confidence</th>
            <th className="text-left py-3 px-4 text-slate-500 font-medium">Status</th>
            <th className="text-left py-3 px-4 text-slate-500 font-medium">Date</th>
            <th className="py-3 px-4"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {invoices.map((inv) => {
            const data = inv.extracted_data || {}
            const needsAction = ['flagged', 'review_required'].includes(inv.status)
            return (
              <tr
                key={inv.id}
                onClick={() => navigate(`/invoice/${inv.id}`)}
                className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
              >
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    {needsAction && <AlertTriangle size={12} className="text-amber-400 shrink-0" />}
                    <span className="text-slate-300 truncate max-w-[140px]" title={inv.file_name}>
                      {inv.file_name}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4 text-slate-300">
                  {data.vendor_name || <span className="text-slate-600">—</span>}
                </td>
                <td className="py-3 px-4 font-mono text-slate-400 text-xs">
                  {data.invoice_number || <span className="text-slate-600">—</span>}
                </td>
                <td className="py-3 px-4 text-right font-mono text-slate-200">
                  {data.total_amount != null
                    ? `₹${Number(data.total_amount).toLocaleString('en-IN')}`
                    : <span className="text-slate-600">—</span>
                  }
                </td>
                <td className="py-3 px-4">
                  <ConfidenceBar score={inv.confidence_score} />
                </td>
                <td className="py-3 px-4">
                  <StatusBadge status={inv.status} />
                </td>
                <td className="py-3 px-4 text-slate-500 text-xs">
                  {new Date(inv.created_at).toLocaleDateString('en-IN')}
                </td>
                <td className="py-3 px-4">
                  <ChevronRight size={14} className="text-slate-600 group-hover:text-slate-400 transition-colors" />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
