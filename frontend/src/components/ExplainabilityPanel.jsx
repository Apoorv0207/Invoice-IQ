import { useState } from 'react'
import { Brain, ChevronDown, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

const DECISION_ICONS = {
  'Invoice Extraction':   { emoji: '🔍', color: 'text-blue-400' },
  'Math Validation':      { emoji: '🔢', color: 'text-purple-400' },
  'Duplicate Detection':  { emoji: '🔁', color: 'text-orange-400' },
  'PO Matching':          { emoji: '📋', color: 'text-cyan-400' },
  'GL Assignment':        { emoji: '📂', color: 'text-emerald-400' },
  'Confidence Routing':   { emoji: '⚖️',  color: 'text-amber-400' },
  'Processing Error':     { emoji: '❌', color: 'text-red-400' },
}

function ConfidenceDot({ value }) {
  const pct = Math.round(value * 100)
  const color = pct >= 90 ? 'bg-emerald-500' : pct >= 70 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-1.5 h-1.5 rounded-full ${color}`} />
      <span className="text-xs font-mono text-slate-400">{pct}%</span>
    </div>
  )
}

function ExplanationCard({ explanation, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const { decision, output, confidence, reason = [] } = explanation
  const cfg = DECISION_ICONS[decision] || { emoji: '🤖', color: 'text-slate-400' }

  return (
    <div className="border border-slate-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-slate-800/50 transition-colors text-left"
      >
        <span className="text-base">{cfg.emoji}</span>
        <div className="flex-1 min-w-0">
          <p className={`text-xs font-medium ${cfg.color}`}>{decision}</p>
          <p className="text-xs text-slate-400 truncate">{output}</p>
        </div>
        <ConfidenceDot value={confidence} />
        {open
          ? <ChevronDown size={12} className="text-slate-500 shrink-0" />
          : <ChevronRight size={12} className="text-slate-500 shrink-0" />
        }
      </button>

      {open && (
        <div className="border-t border-slate-800 px-3 py-3 bg-slate-900/50">
          <p className="text-xs text-slate-500 uppercase tracking-wider font-medium mb-2">
            Reasoning
          </p>
          <ul className="space-y-1.5">
            {reason.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                <ChevronRight size={10} className="mt-0.5 shrink-0 text-slate-600" />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default function ExplainabilityPanel({ explanations = [], loading = false }) {
  const [allOpen, setAllOpen] = useState(false)

  if (loading) {
    return (
      <div className="text-center py-6 text-slate-600 text-sm">
        Loading explanations...
      </div>
    )
  }

  if (!explanations.length) {
    return (
      <div className="text-center py-6 text-slate-600 text-sm">
        No explanations available yet
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain size={14} className="text-brand-400" />
          <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">
            AI Decision Trail
          </p>
        </div>
        <button
          onClick={() => setAllOpen(o => !o)}
          className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          {allOpen ? 'Collapse all' : 'Expand all'}
        </button>
      </div>

      <div className="space-y-1.5">
        {explanations.map((exp, i) => (
          <ExplanationCard
            key={i}
            explanation={exp}
            defaultOpen={allOpen || exp.decision === 'Confidence Routing'}
          />
        ))}
      </div>

      <p className="text-xs text-slate-600 text-center pt-1">
        {explanations.length} decisions recorded for this invoice
      </p>
    </div>
  )
}