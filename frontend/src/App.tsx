import { useState } from 'react'
import { Shield } from 'lucide-react'
import FileExplorer from './components/FileExplorer'
import Dashboard from './components/Dashboard'
import CopilotChat from './components/CopilotChat'
import AgentProgressTracker from './components/AgentProgressTracker'
import ConnectionStatus from './components/ConnectionStatus'
import { AgentProgress } from './types'

function App() {
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null)
  const [agentProgress, setAgentProgress] = useState<AgentProgress | null>(null)
  const [, setShowProgress] = useState(false)

  return (
    <div className="h-screen overflow-hidden bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">LogSentinel AI</h1>
              <p className="text-sm text-gray-400">CRITICAL INFRASTRUCTURE PROTECTION</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ConnectionStatus />
          </div>
        </div>
      </header>

      {/* Multi-Agent Workflow Progress */}
      <AgentProgressTracker currentProgress={agentProgress} visible={true} />

      {/* Analysis Complete Badge */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-2">
        <div className="flex justify-end">
          <div className="bg-green-600 px-3 py-1 rounded text-sm font-medium">
            ANALYSIS COMPLETE
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Files Panel - Left */}
        <div className="w-80 bg-gray-900 border-r border-gray-700 flex flex-col overflow-hidden">
          <FileExplorer
            onFileSelect={setSelectedFileId}
            selectedFileId={selectedFileId}
          />
        </div>

        {/* Dashboard - Center (with scrollbar) */}
        <div className="flex-1 bg-gray-800 flex flex-col overflow-hidden">
          <Dashboard fileId={selectedFileId} />
        </div>

        {/* AI Copilot - Right (Dark theme) */}
        <div className="w-[420px] bg-gray-900 border-l border-gray-700 flex flex-col overflow-hidden">
          <CopilotChat
            fileId={selectedFileId}
            onProgressUpdate={setAgentProgress}
            onProgressVisibilityChange={setShowProgress}
          />
        </div>
      </main>
    </div>
  )
}

export default App
