import { CheckCircle, AlertTriangle, HelpCircle, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

const STATUS_CONFIG = {
  PASS:    { label: 'PO Matched',     color: 'emerald', Icon: CheckCircle },
  FLAGGED: { label: 'PO Mismatch',    color: 'amber',   Icon: AlertTriangle },
  MISSING: { label: 'No PO Found',    color: 'slate',   Icon: HelpCircle },
}

function CompareRow({ label, invoiceVal, poVal, diffPct, isMismatch }) {
  return (
    <div className={clsx(
      'grid grid-cols-3 gap-2 py-2 px-3 rounded-lg text-sm',
      isMismatch ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-slate-800/40'
    )}>
      <span className="text-slate-500 text-xs self-center">{label}</span>
      <div className="text-center">
        <p className="text-xs text-slate-600 mb-0.5">Invoice</p>
        <p className={clsx('font-mono text-xs', isMismatch ? 'text-amber-300' : 'text-slate-300')}>
          {invoiceVal ?? '—'}
        </p>
      </div>
      <div className="text-center">
        <p className="text-xs text-slate-600 mb-0.5">PO</p>
        <p className="font-mono text-xs text-slate-300">{poVal ?? '—'}</p>
        {isMismatch && diffPct != null && (
          <p className="text-xs text-amber-400 mt-0.5">+{diffPct}% variance</p>
        )}
      </div>
    </div>
  )
}

export default function POMatchPanel({ poMatch, invoiceData }) {
  if (!poMatch) {
    return (
      <div className="text-slate-600 text-sm text-center py-4">
        No PO matching data available
      </div>
    )
  }

  const { po_status, mismatches = [], summary, po_number, po_vendor, po_total } = poMatch
  const cfg = STATUS_CONFIG[po_status] || STATUS_CONFIG['MISSING']
  const { label, color, Icon } = cfg

  const mismatchFields = new Set(mismatches.map(m => m.field))

  return (
    <div className="space-y-3">
      {/* Status header */}
      <div className={clsx(
        'flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium',
        color === 'emerald' && 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
        color === 'amber' && 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
        color === 'slate' && 'bg-slate-800 text-slate-400 border border-slate-700',
      )}>
        <Icon size={14} />
        {label}
        {po_number && <span className="font-mono text-xs ml-auto opacity-70">PO# {po_number}</span>}
      </div>

      {summary && (
        <p className="text-xs text-slate-500 px-1">{summary}</p>
      )}

      {/* Side-by-side comparison */}
      {po_status !== 'MISSING' && invoiceData && (
        <div className="space-y-1.5">
          <p className="text-xs text-slate-500 uppercase tracking-wider font-medium px-1">
            Field Comparison
          </p>

          <CompareRow
            label="Vendor"
            invoiceVal={invoiceData.vendor_name}
            poVal={po_vendor}
            isMismatch={false}
          />
          <CompareRow
            label="Total (₹)"
            invoiceVal={invoiceData.total_amount?.toLocaleString('en-IN')}
            poVal={po_total?.toLocaleString('en-IN')}
            isMismatch={mismatchFields.has('total_amount')}
            diffPct={mismatches.find(m => m.field === 'total_amount')?.difference_percent}
          />
          <CompareRow
            label="Tax (₹)"
            invoiceVal={invoiceData.tax_amount?.toLocaleString('en-IN')}
            poVal="—"
            isMismatch={mismatchFields.has('tax_amount')}
            diffPct={mismatches.find(m => m.field === 'tax_amount')?.difference_percent}
          />

          {/* Line item mismatches */}
          {mismatches.filter(m => m.field.startsWith('line_')).map((m, i) => (
            <CompareRow
              key={i}
              label={m.field.replace(/_/g, ' ')}
              invoiceVal={m.invoice_value}
              poVal={m.po_value}
              isMismatch={true}
              diffPct={m.difference_percent}
            />
          ))}
        </div>
      )}

      {/* Mismatch list */}
      {mismatches.length > 0 && (
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-3">
          <p className="text-xs text-amber-400 font-medium mb-2">
            {mismatches.length} mismatch(es) detected
          </p>
          {mismatches.map((m, i) => (
            <p key={i} className="text-xs text-amber-300/80 flex items-start gap-1.5 mb-1">
              <ChevronRight size={10} className="mt-0.5 shrink-0" />
              <span>
                <span className="font-mono">{m.field}</span>: invoice={m.invoice_value}, PO={m.po_value}
                <span className="text-amber-500 ml-1">({m.difference_percent}% variance)</span>
              </span>
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
