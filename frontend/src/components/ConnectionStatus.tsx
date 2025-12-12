import React, { useState, useEffect, useRef } from 'react'
import { CheckCircle, XCircle, Loader, Wifi, Database } from 'lucide-react'
import axios from 'axios'

const ConnectionStatus: React.FC = () => {
  const [status, setStatus] = useState<{
    backend: 'loading' | 'connected' | 'failed'
    database: 'loading' | 'connected' | 'failed'
    showDetails: boolean
  }>({
    backend: 'loading',
    database: 'loading',
    showDetails: false
  })

  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setStatus(prev => ({ ...prev, showDetails: false }))
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    const testConnections = async () => {
      const apiBase = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '/api' : 'https://hackathon-logsentinel.onrender.com/api')
      
      try {
        // Test backend connection
        const response = await axios.get(`${apiBase.replace('/api', '')}/health`, {
          timeout: 5000
        })

        if (response.status === 200) {
          setStatus(prev => ({ ...prev, backend: 'connected' }))
          
          // Test database connection
          try {
            await axios.get(`${apiBase}/files`, { timeout: 5000 })
            setStatus(prev => ({ ...prev, database: 'connected' }))
          } catch {
            setStatus(prev => ({ ...prev, database: 'failed' }))
          }
        }
      } catch {
        setStatus(prev => ({
          ...prev,
          backend: 'failed',
          database: 'failed'
        }))
      }
    }

    testConnections()
    const interval = setInterval(testConnections, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (state: 'loading' | 'connected' | 'failed') => {
    switch (state) {
      case 'loading':
        return <Loader className="w-3 h-3 animate-spin text-yellow-400" />
      case 'connected':
        return <CheckCircle className="w-3 h-3 text-green-400" />
      case 'failed':
        return <XCircle className="w-3 h-3 text-red-400" />
    }
  }

  const isOnline = status.backend === 'connected' && status.database === 'connected'
  const hasIssues = status.backend === 'failed' || status.database === 'failed'
  const isLoading = status.backend === 'loading' || status.database === 'loading'

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Main Status Indicator */}
      <div 
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-700/50 border border-gray-600/50 hover:bg-gray-700/70 transition-all cursor-pointer select-none"
        onClick={() => setStatus(prev => ({ ...prev, showDetails: !prev.showDetails }))}
      >
        <div className={`w-2 h-2 rounded-full transition-all duration-300 ${
          isLoading ? 'bg-yellow-400 animate-pulse' : 
          isOnline ? 'bg-green-400 shadow-sm shadow-green-400/50' : 
          'bg-red-400 shadow-sm shadow-red-400/50'
        }`}></div>
        <span className={`text-sm font-medium transition-colors ${
          isLoading ? 'text-yellow-400' :
          isOnline ? 'text-green-400' : 'text-red-400'
        }`}>
          {isLoading ? 'Connecting...' :
           isOnline ? 'System Online' : 'System Issues'}
        </span>
        <div className={`text-gray-400 transition-transform duration-200 ${
          status.showDetails ? 'rotate-180' : ''
        }`}>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Detailed Status Dropdown */}
      {status.showDetails && (
        <div className="absolute top-full right-0 mt-2 w-64 bg-gray-800 border border-gray-600 rounded-lg shadow-xl shadow-black/20 z-50 overflow-hidden">
          <div className="p-3 border-b border-gray-700">
            <h4 className="text-sm font-semibold text-gray-200 mb-2">System Status</h4>
            
            {/* Backend Status */}
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <Wifi className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-300">Backend API</span>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(status.backend)}
                <span className={`text-xs font-medium ${
                  status.backend === 'connected' ? 'text-green-400' :
                  status.backend === 'failed' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {status.backend === 'connected' ? 'Connected' :
                   status.backend === 'failed' ? 'Offline' : 'Connecting'}
                </span>
              </div>
            </div>

            {/* Database Status */}
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-300">Database</span>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(status.database)}
                <span className={`text-xs font-medium ${
                  status.database === 'connected' ? 'text-green-400' :
                  status.database === 'failed' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {status.database === 'connected' ? 'Connected' :
                   status.database === 'failed' ? 'Offline' : 'Connecting'}
                </span>
              </div>
            </div>
          </div>
          
          {/* Overall Status */}
          <div className={`p-3 text-xs ${
            isOnline ? 'bg-green-900/30 text-green-300' :
            hasIssues ? 'bg-red-900/30 text-red-300' : 
            'bg-yellow-900/30 text-yellow-300'
          }`}>
            {isOnline ? '✓ All systems operational' :
             hasIssues ? '⚠ System experiencing issues' :
             '⏳ Systems initializing...'}
          </div>
        </div>
      )}
    </div>
  )
}

export default ConnectionStatus