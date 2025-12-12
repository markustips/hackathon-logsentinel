export interface LogFile {
  id: string
  filename: string
  file_size: number
  upload_time: string
  status: string
  total_records: number
  error_message?: string
}

export interface SearchResult {
  record_id: string
  chunk_id: string
  timestamp?: string
  log_level?: string
  source?: string
  message: string
  score: number
}

export interface Anomaly {
  id: string
  record_id: string
  timestamp?: string
  anomaly_type: string
  score: number
  severity: string
  description: string
  message: string
  mitre_techniques: string[]
}

export interface CopilotMessage {
  role: 'user' | 'assistant'
  content: string
  agent?: string
  references?: string[]
}

export interface MitreTechnique {
  id: string
  name: string
  tactic: string
  url: string
}

export interface AgentProgress {
  step: 'query_received' | 'orchestrator_routing' | 'log_analyst' | 'anomaly_hunter' | 'threat_mapper' | 'synthesizing_results' | 'complete'
  agent?: string
  message?: string
}

export interface StreamEvent {
  type: 'status' | 'result' | 'error'
  step?: string
  agent?: string
  message?: string
  references?: string[]
  mitre_techniques?: MitreTechnique[]
  metadata?: any
}
