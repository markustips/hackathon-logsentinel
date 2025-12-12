import { ExternalLink } from 'lucide-react'
import { MitreTechnique } from '../types'

interface MitreBadgeProps {
  technique: MitreTechnique
  size?: 'sm' | 'md'
}

export default function MitreBadge({ technique, size = 'md' }: MitreBadgeProps) {
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-1' : 'text-sm px-3 py-1.5'

  return (
    <a
      href={technique.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center gap-1.5 bg-purple-900/40 hover:bg-purple-900/60 border border-purple-700 text-purple-300 rounded-lg transition-colors ${sizeClasses}`}
    >
      <span className="font-mono font-semibold">{technique.id}</span>
      <span className="hidden sm:inline">- {technique.name}</span>
      <ExternalLink className="w-3 h-3" />
    </a>
  )
}
