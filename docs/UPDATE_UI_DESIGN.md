# UI Design Update Instructions

## Overview
This document provides the code to update LogSentinel AI's UI to a modern, polished design while keeping all existing functionality.

## Files to Update

### 1. Update `frontend/tailwind.config.js`

Replace the entire file with:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a',      // slate-900
        surface: '#1e293b',         // slate-800
        surfaceLight: '#334155',    // slate-700
        primary: '#3b82f6',         // blue-500
        accent: '#10b981',          // emerald-500
        warning: '#f59e0b',         // amber-500
        secondary: '#94a3b8',       // slate-400
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
      }
    },
  },
  plugins: [],
}
```

### 2. Update `frontend/src/App.tsx`

Replace with the modern layout while keeping existing functionality:

```typescript
import { useState } from 'react'
import { Shield } from 'lucide-react'
import FileExplorer from './components/FileExplorer'
import Dashboard from './components/Dashboard'
import CopilotChat from './components/CopilotChat'
import AgentProgressTracker from './components/AgentProgressTracker'
import { AgentProgress } from './types'

function App() {
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null)
  const [agentProgress, setAgentProgress] = useState<AgentProgress | null>(null)
  const [showProgress, setShowProgress] = useState(false)

  return (
    <div className="flex flex-col h-screen bg-background text-slate-200 font-sans selection:bg-blue-500/30">

      {/* Top Header */}
      <header className="h-16 flex items-center justify-between px-6 bg-surface border-b border-surfaceLight shrink-0 z-20 shadow-md">
        <div className="flex items-center gap-3">
          <div className="bg-primary p-2 rounded-lg shadow-[0_0_15px_rgba(59,130,246,0.5)]">
            <Shield className="text-white" size={24} />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white">LogSentinel AI</h1>
            <p className="text-[10px] text-blue-400 font-medium uppercase tracking-wider">Critical Infrastructure Protection</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                <span className="text-xs font-medium text-emerald-500">System Online</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-surfaceLight flex items-center justify-center border border-slate-600 text-xs">
                AI
            </div>
        </div>
      </header>

      {/* Workflow Progress Bar */}
      <AgentProgressTracker currentProgress={agentProgress} visible={true} />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">

        {/* Left Sidebar: File Explorer */}
        <div className="w-80 shrink-0">
          <FileExplorer
            onFileSelect={setSelectedFileId}
            selectedFileId={selectedFileId}
          />
        </div>

        {/* Center & Right Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Center Dashboard */}
          <div className="flex-1 min-w-0">
            <Dashboard fileId={selectedFileId} />
          </div>

          {/* Right Sidebar: Chat */}
          <div className="w-96 shrink-0 border-l border-surfaceLight">
            <CopilotChat
              fileId={selectedFileId}
              onProgressUpdate={setAgentProgress}
              onProgressVisibilityChange={setShowProgress}
            />
          </div>
        </div>

      </div>
    </div>
  )
}

export default App
```

### 3. Update `frontend/src/components/AgentProgressTracker.tsx`

Update the styling to match the new design:

Find and replace the return statement styles:

```typescript
return (
  <div className="w-full bg-surface border-b border-surfaceLight py-4 px-6">
    <div className="flex flex-col space-y-2">
      <div className="flex items-center justify-between text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
        <span>Multi-Agent Workflow Progress</span>
        <span className={currentProgress?.step === 'complete' ? "text-accent" : "text-blue-400 animate-pulse"}>
          {currentProgress?.step === 'complete' ? "Analysis Complete" : "Processing..."}
        </span>
      </div>

      <div className="relative flex items-center justify-between">
        {/* Connecting Line */}
        <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-0.5 bg-surfaceLight -z-0"></div>

        {/* Progress Line */}
        <div
          className="absolute left-0 top-1/2 transform -translate-y-1/2 h-0.5 bg-accent transition-all duration-500 ease-out -z-0"
          style={{ width: `${Math.min(100, (currentStepIndex / (PROGRESS_STEPS.length - 1)) * 100)}%` }}
        ></div>

        {PROGRESS_STEPS.map((step, index) => {
          const Icon = step.icon
          const isActive = index === currentStepIndex && !isComplete
          const isCompleted = index < currentStepIndex || (index === currentStepIndex && isComplete)
          const isPending = index > currentStepIndex

          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center group">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300 bg-surface
                ${isCompleted ? 'border-accent text-accent' : isActive ? 'border-blue-500 text-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]' : 'border-surfaceLight text-surfaceLight'}`}
              >
                {isCompleted ? (
                  <Check className="w-4 h-4" />
                ) : isActive ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <span
                className={`absolute top-10 text-[10px] font-medium whitespace-nowrap transition-colors duration-300
                ${isCompleted ? 'text-accent' : isActive ? 'text-blue-400' : 'text-slate-500'}`}
              >
                {step.label}
              </span>
            </div>
          )
        })}
      </div>

      {currentProgress?.message && (
        <div className="text-center mt-2">
          <p className="text-xs text-slate-400">{currentProgress.message}</p>
        </div>
      )}
    </div>
  </div>
)
```

## Installation

1. First, make sure you have recharts installed for charts:
```bash
cd frontend
npm install recharts
```

2. Update each file manually by copying the code above, or use the automated script provided below.

3. Restart the dev server:
```bash
npm run dev
```

## Key Design Changes

- **Color Scheme**: Modern dark theme with slate blues
- **Header**: Cleaner with glowing icon and status indicator
- **Progress Tracker**: Horizontal stepper with animated progress bar
- **Layout**: Three-column layout (files | dashboard | chat)
- **Typography**: Better hierarchy with varied font sizes
- **Spacing**: More breathing room and consistent padding
- **Effects**: Subtle shadows, glows, and transitions

## Functionality Preserved

All existing functionality remains intact:
- ✅ File upload and selection
- ✅ Multi-agent workflow tracking
- ✅ Real-time progress updates
- ✅ Copilot chat with streaming
- ✅ Anomaly detection display
- ✅ MITRE ATT&CK technique badges
- ✅ Dashboard statistics
