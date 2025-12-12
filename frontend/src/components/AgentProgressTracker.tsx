import { Check, Loader, Brain, Search, TrendingUp, Shield, Sparkles } from 'lucide-react'
import { AgentProgress } from '../types'

interface AgentProgressTrackerProps {
  currentProgress: AgentProgress | null
  visible: boolean
}

const PROGRESS_STEPS = [
  {
    id: 'query_received',
    label: 'Query Received',
    icon: Sparkles
  },
  {
    id: 'orchestrator_routing',
    label: 'Orchestrator',
    icon: Brain
  },
  {
    id: 'log_analyst',
    label: 'Log Analyst',
    icon: Search
  },
  {
    id: 'anomaly_hunter',
    label: 'Anomaly Hunter',
    icon: TrendingUp
  },
  {
    id: 'threat_mapper',
    label: 'Threat Mapper',
    icon: Shield
  },
  {
    id: 'synthesizing_results',
    label: 'Synthesizing',
    icon: Brain
  },
  {
    id: 'complete',
    label: 'Complete',
    icon: Check
  }
]

export default function AgentProgressTracker({ currentProgress, visible }: AgentProgressTrackerProps) {
  if (!visible) return null

  const getCurrentStepIndex = () => {
    if (!currentProgress) return 0
    return PROGRESS_STEPS.findIndex(step => step.id === currentProgress.step)
  }

  const currentStepIndex = getCurrentStepIndex()
  const isComplete = currentProgress?.step === 'complete'

  return (
    <div className="w-full bg-gray-800 border-b border-gray-700 py-4 px-6">
      <div className="flex flex-col space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider">
          <span>Multi-Agent Workflow Progress</span>
          {currentProgress?.message && (
            <span className="text-blue-400 normal-case font-normal">{currentProgress.message}</span>
          )}
        </div>

        <div className="relative flex items-center justify-between">
          {/* Background connecting line */}
          <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-0.5 bg-gray-700 z-0"></div>

          {/* Progress line */}
          <div
            className="absolute left-0 top-1/2 transform -translate-y-1/2 h-0.5 bg-green-500 transition-all duration-500 ease-out z-0"
            style={{ width: `${Math.min(100, (currentStepIndex / (PROGRESS_STEPS.length - 1)) * 100)}%` }}
          ></div>

          {/* Step circles */}
          {PROGRESS_STEPS.map((step, index) => {
            const Icon = step.icon
            const isActive = index === currentStepIndex && !isComplete
            const isCompleted = index < currentStepIndex || (index === currentStepIndex && isComplete)

            return (
              <div key={step.id} className="relative z-10 flex flex-col items-center group">
                {/* Circle */}
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 bg-gray-800
                    ${isCompleted ? 'border-green-500 text-green-500' : isActive ? 'border-blue-500 text-blue-500 animate-pulse' : 'border-gray-700 text-gray-500'}`}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5" />
                  ) : isActive ? (
                    <Loader className="w-5 h-5 animate-spin" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </div>

                {/* Label */}
                <span
                  className={`absolute top-12 text-[10px] font-medium whitespace-nowrap transition-colors duration-300
                    ${isCompleted ? 'text-green-400' : isActive ? 'text-blue-400' : 'text-gray-500'}`}
                >
                  {step.label}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
