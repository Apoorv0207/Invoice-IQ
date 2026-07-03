import { Download, FileJson, FileSpreadsheet, ChevronDown } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import { exportCsv, exportJson } from '../utils/api'

export default function ExportButton({ invoiceId }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => { if (!ref.current?.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className="btn-ghost flex items-center gap-1.5"
      >
        <Download size={14} />
        Export
        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 bg-slate-800 border border-slate-700 rounded-lg overflow-hidden shadow-xl z-10 min-w-[160px]">
          <button
            onClick={() => { exportCsv(invoiceId); setOpen(false) }}
            className="flex items-center gap-2 w-full px-3 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
          >
            <FileSpreadsheet size={14} className="text-emerald-400" />
            Export as CSV
          </button>
          <button
            onClick={() => { exportJson(invoiceId); setOpen(false) }}
            className="flex items-center gap-2 w-full px-3 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
          >
            <FileJson size={14} className="text-brand-400" />
            Export as JSON
          </button>
        </div>
      )}
    </div>
  )
}
