import { useState } from 'react'
import { CheckCircle, XCircle, Edit3, Save, X, AlertTriangle, Copy } from 'lucide-react'
import { reviewInvoice, updateField } from '../utils/api'
import clsx from 'clsx'

const EDITABLE_FIELDS = [
  { key: 'vendor_name',     label: 'Vendor Name' },
  { key: 'invoice_number',  label: 'Invoice #' },
  { key: 'invoice_date',    label: 'Invoice Date' },
  { key: 'due_date',        label: 'Due Date' },
  { key: 'po_number',       label: 'PO Number' },
  { key: 'total_amount',    label: 'Total Amount' },
  { key: 'tax_amount',      label: 'Tax Amount' },
  { key: 'subtotal',        label: 'Subtotal' },
  { key: 'payment_terms',   label: 'Payment Terms' },
]

function EditableField({ invoiceId, fieldKey, label, value, isFlagged, onSaved }) {
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState(value || '')
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await updateField(invoiceId, fieldKey, val)
      onSaved(fieldKey, val)
      setEditing(false)
    } catch (e) {
      console.error(e)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={clsx(
      'flex items-center justify-between py-2.5 px-3 rounded-lg group',
      isFlagged ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-slate-800/50'
    )}>
      <div className="flex items-center gap-2 min-w-0">
        {isFlagged && <AlertTriangle size={12} className="text-amber-400 shrink-0" />}
        <span className="text-slate-500 text-xs w-28 shrink-0">{label}</span>
        {editing ? (
          <input
            autoFocus
            value={val}
            onChange={e => setVal(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') save(); if (e.key === 'Escape') setEditing(false) }}
            className="bg-slate-700 text-slate-100 text-sm px-2 py-0.5 rounded border border-brand-500 outline-none flex-1 min-w-0"
          />
        ) : (
          <span className={clsx('text-sm font-mono truncate', value ? 'text-slate-200' : 'text-slate-600 italic')}>
            {value || 'not found'}
          </span>
        )}
      </div>
      <div className="flex items-center gap-1 shrink-0 ml-2">
        {editing ? (
          <>
            <button onClick={save} disabled={saving} className="text-emerald-400 hover:text-emerald-300 p-1">
              <Save size={13} />
            </button>
            <button onClick={() => setEditing(false)} className="text-slate-500 hover:text-slate-300 p-1">
              <X size={13} />
            </button>
          </>
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="text-slate-600 hover:text-slate-400 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Edit3 size={13} />
          </button>
        )}
      </div>
    </div>
  )
}

export default function ReviewPanel({ invoice, onReviewed }) {
  const [submitting, setSubmitting] = useState(null)
  const [localData, setLocalData] = useState(invoice.extracted_data || {})

  const flaggedFields = invoice.validation?.flagged_fields || []

  const handleReview = async (action) => {
    setSubmitting(action)
    try {
      await reviewInvoice(invoice.id, action, localData)
      if (onReviewed) onReviewed()
    } catch (e) {
      console.error(e)
    } finally {
      setSubmitting(null)
    }
  }

  const handleFieldSaved = (field, value) => {
    setLocalData(prev => ({ ...prev, [field]: value }))
  }

  const needsReview = ['flagged', 'review_required'].includes(invoice.status)

  return (
    <div className="space-y-4">
      {/* Routing reason */}
      {invoice.routing_reason && (
        <div className={clsx(
          'text-sm px-3 py-2 rounded-lg',
          needsReview ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20' : 'bg-slate-800 text-slate-400'
        )}>
          {invoice.routing_reason}
        </div>
      )}

      {/* Validation issues */}
      {invoice.validation?.is_duplicate && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-sm text-red-400">
          ⚠️ Duplicate detected — same invoice may have been posted already
        </div>
      )}
      {invoice.validation?.math_valid === false && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2 text-sm text-amber-400">
          ⚠️ Math mismatch detected — line items don't add up to total
          {invoice.validation.math_discrepancy != null && (
            <span className="font-mono ml-1">(diff: ₹{invoice.validation.math_discrepancy})</span>
          )}
        </div>
      )}

      {/* Editable fields */}
      <div className="space-y-1.5">
        <p className="text-xs text-slate-500 uppercase tracking-wider font-medium px-1">
          {needsReview ? 'Review & Correct Fields' : 'Extracted Fields'}
        </p>
        {EDITABLE_FIELDS.map(({ key, label }) => (
          <EditableField
            key={key}
            invoiceId={invoice.id}
            fieldKey={key}
            label={label}
            value={localData[key]}
            isFlagged={flaggedFields.includes(key)}
            onSaved={handleFieldSaved}
          />
        ))}
      </div>

      {/* Action buttons */}
      {needsReview && (
        <div className="flex gap-2 pt-2">
          <button
            onClick={() => handleReview('approve')}
            disabled={!!submitting}
            className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50"
          >
            <CheckCircle size={15} />
            {submitting === 'approve' ? 'Approving...' : 'Approve'}
          </button>
          <button
            onClick={() => handleReview('reject')}
            disabled={!!submitting}
            className="flex-1 flex items-center justify-center gap-2 bg-slate-700 hover:bg-red-900/60 text-slate-300 hover:text-red-300 text-sm font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50"
          >
            <XCircle size={15} />
            {submitting === 'reject' ? 'Rejecting...' : 'Reject'}
          </button>
        </div>
      )}

      {/* Already reviewed note */}
      {['approved', 'rejected', 'auto_approved'].includes(invoice.status) && (
        <div className="text-xs text-slate-500 text-center pt-1">
          {invoice.status === 'auto_approved'
            ? '✓ Auto-approved with high confidence — no review required'
            : `✓ Reviewed ${invoice.reviewed_by ? `by ${invoice.reviewed_by}` : ''}`
          }
        </div>
      )}
    </div>
  )
}
