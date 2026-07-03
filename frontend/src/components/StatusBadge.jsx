import { CheckCircle, Clock, AlertTriangle, XCircle, Eye, Zap } from 'lucide-react'

const STATUS_CONFIG = {
  processing:     { label: 'Processing',    cls: 'badge-processing', Icon: Clock },
  auto_approved:  { label: 'Auto Approved', cls: 'badge-auto',       Icon: Zap },
  flagged:        { label: 'Flagged',       cls: 'badge-flagged',    Icon: AlertTriangle },
  review_required:{ label: 'Review Needed', cls: 'badge-review',     Icon: Eye },
  approved:       { label: 'Approved',      cls: 'badge-approved',   Icon: CheckCircle },
  rejected:       { label: 'Rejected',      cls: 'badge-rejected',   Icon: XCircle },
}

export default function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG['processing']
  const { label, cls, Icon } = cfg
  return (
    <span className={cls}>
      <Icon size={11} />
      {label}
    </span>
  )
}
