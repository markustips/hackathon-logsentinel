import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Loader, Brain, Search, TrendingUp, Shield, Sparkles } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { CopilotMessage, MitreTechnique, AgentProgress } from '../types'
import MitreBadge from './MitreBadge'
import MarkdownRenderer from './MarkdownRenderer'

interface CopilotChatProps {
  fileId: string | null
  onProgressUpdate: (progress: AgentProgress | null) => void
  onProgressVisibilityChange: (visible: boolean) => void
}

const SUGGESTED_QUERIES = [
  "What anomalies were detected?",
  "Show me authentication failures",
  "What MITRE ATT&CK techniques are present?",
  "What caused the reactor failure?",
  "Show me the attack timeline"
]

const AGENT_ICONS = {
  'orchestrator': Brain,
  'log_analyst': Search,
  'anomaly_hunter': TrendingUp,
  'threat_mapper': Shield
}

const AGENT_COLORS = {
  'orchestrator': 'text-blue-400 bg-blue-900/40',
  'log_analyst': 'text-green-400 bg-green-900/40',
  'anomaly_hunter': 'text-yellow-400 bg-yellow-900/40',
  'threat_mapper': 'text-purple-400 bg-purple-900/40'
}

export default function CopilotChat({ fileId, onProgressUpdate, onProgressVisibilityChange }: CopilotChatProps) {
  const [messages, setMessages] = useState<CopilotMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentAgent, setCurrentAgent] = useState<string | null>(null)
  const [mitreTechniques, setMitreTechniques] = useState<MitreTechnique[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const api = useApi()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (fileId) {
      setMessages([])
      setMitreTechniques([])
    }
  }, [fileId])

  const handleSend = async (query?: string) => {
    const messageText = query || input
    if (!messageText.trim() || !fileId || loading) return

    const userMessage: CopilotMessage = {
      role: 'user',
      content: messageText
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setCurrentAgent('orchestrator')
    onProgressVisibilityChange(true)
    onProgressUpdate({ step: 'query_received', message: 'Query received' })

    try {
      await api.chatWithCopilotStream(
        fileId,
        messageText,
        messages,
        (event) => {
          if (event.step) {
            onProgressUpdate({
              step: event.step,
              agent: event.agent,
              message: event.message
            })
            setCurrentAgent(event.agent || 'orchestrator')
          }
        },
        (result) => {
          const assistantMessage: CopilotMessage = {
            role: 'assistant',
            content: result.message,
            agent: result.agent,
            references: result.references
          }

          setMessages(prev => [...prev, assistantMessage])

          if (result.mitre_techniques && result.mitre_techniques.length > 0) {
            setMitreTechniques(prev => {
              const existingIds = new Set(prev.map(t => t.id))
              const newTechniques = result.mitre_techniques.filter(
                (t: MitreTechnique) => !existingIds.has(t.id)
              )
              return [...prev, ...newTechniques]
            })
          }

          setLoading(false)
          setCurrentAgent(null)
          onProgressUpdate({
            step: 'complete',
            message: 'Analysis complete'
          })
        },
        (error) => {
          console.error('Copilot error:', error)
          const errorMessage: CopilotMessage = {
            role: 'assistant',
            content: 'I encountered an error processing your request. Please try again.'
          }
          setMessages(prev => [...prev, errorMessage])
          setLoading(false)
          setCurrentAgent(null)
        }
      )
    } catch (error) {
      console.error('Copilot error:', error)
      const errorMessage: CopilotMessage = {
        role: 'assistant',
        content: 'I encountered an error processing your request. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
      setLoading(false)
      setCurrentAgent(null)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const getAgentBadge = (agent?: string) => {
    if (!agent) return null

    const agents = agent.split(', ')
    return (
      <div className="flex flex-wrap gap-1 mt-2">
        {agents.map((agentName) => {
          const Icon = AGENT_ICONS[agentName as keyof typeof AGENT_ICONS] || Brain
          const colorClass = AGENT_COLORS[agentName as keyof typeof AGENT_COLORS] || 'text-gray-400 bg-gray-800'

          return (
            <div
              key={agentName}
              className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${colorClass}`}
            >
              <Icon className="w-3 h-3" />
              <span className="capitalize">{agentName.replace('_', ' ')}</span>
            </div>
          )
        })}
      </div>
    )
  }

  if (!fileId) {
    return (
      <div className="h-full flex items-center justify-center p-6 bg-gray-900">
        <div className="text-center text-gray-400">
          <Bot className="w-16 h-16 mx-auto mb-4 opacity-30" />
          <p className="text-sm">Select a file to start chatting</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Copilot</h2>
            <p className="text-xs text-gray-400">Multi-Agent SOC Analyst</p>
          </div>
        </div>
      </div>

      {/* MITRE Techniques */}
      {mitreTechniques.length > 0 && (
        <div className="flex-shrink-0 mx-6 mt-4 p-3 bg-purple-900/20 border border-purple-700/50 rounded-lg">
          <p className="text-xs font-semibold text-purple-300 mb-2">MITRE ATT&CK Techniques</p>
          <div className="flex flex-wrap gap-2">
            {mitreTechniques.map((tech) => (
              <MitreBadge key={tech.id} technique={tech} size="sm" />
            ))}
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {/* Welcome Message */}
        {messages.length === 0 && (
          <div className="mb-6">
            <div className="flex gap-3 mb-6">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <div className="bg-gray-800 rounded-2xl rounded-tl-none p-4 border border-gray-700">
                  <h3 className="text-white font-semibold mb-2">Hello! I'm your AI security assistant.</h3>
                  <p className="text-gray-300 text-sm mb-3">I've analyzed your uploaded logs. I can help you with:</p>
                  <ul className="text-gray-300 text-sm space-y-1.5">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span>Identifying attack vectors and anomalies</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span>Correlating timestamps and events</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span>Mapping threats to MITRE ATT&CK</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Suggested Prompts */}
            <div className="space-y-2">
              <p className="text-xs text-gray-400 font-medium px-1">Suggested prompts:</p>
              {SUGGESTED_QUERIES.slice(0, 3).map((query, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(query)}
                  disabled={loading}
                  className="w-full text-left px-4 py-3 bg-gray-800 border border-gray-700 hover:border-blue-500 hover:bg-gray-750 rounded-xl text-sm text-gray-300 transition-all disabled:opacity-50"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat History */}
        <div className="space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className="flex gap-3">
              {msg.role === 'assistant' ? (
                <>
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="bg-gray-800 rounded-2xl rounded-tl-none p-4 border border-gray-700">
                      <MarkdownRenderer content={msg.content} />
                    </div>
                    {msg.agent && getAgentBadge(msg.agent)}
                  </div>
                </>
              ) : (
                <>
                  <div className="flex-1"></div>
                  <div className="max-w-[75%]">
                    <div className="bg-blue-600 text-white rounded-2xl rounded-tr-none p-4">
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                  <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-white" />
                  </div>
                </>
              )}
            </div>
          ))}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="bg-gray-800 rounded-2xl rounded-tl-none p-4 border border-gray-700">
                <div className="flex items-center gap-2">
                  <Loader className="w-4 h-4 animate-spin text-blue-400" />
                  <span className="text-sm text-gray-300">
                    {currentAgent ? `${currentAgent.replace('_', ' ')} is analyzing...` : 'Thinking...'}
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="flex-shrink-0 border-t border-gray-700 p-4 bg-gray-900">
        <div className="relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask Copilot..."
            disabled={loading}
            rows={1}
            className="w-full px-4 py-3 pr-12 bg-gray-800 border border-gray-700 rounded-3xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:opacity-50"
            style={{ minHeight: '44px', maxHeight: '120px' }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement
              target.style.height = 'auto'
              target.style.height = Math.min(target.scrollHeight, 120) + 'px'
            }}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="absolute right-2 bottom-2 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">
          AI can make mistakes. Verify critical information.
        </p>
      </div>
    </div>
  )
}
