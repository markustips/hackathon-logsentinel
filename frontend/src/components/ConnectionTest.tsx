import React, { useState, useEffect } from 'react'
import axios from 'axios'

const ConnectionTest: React.FC = () => {
  const [status, setStatus] = useState<{
    backend: 'loading' | 'connected' | 'failed'
    database: 'loading' | 'connected' | 'failed'
    apiUrl: string
    error?: string
  }>({
    backend: 'loading',
    database: 'loading',
    apiUrl: import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '/api' : 'https://hackathon-logsentinel.onrender.com/api')
  })

  useEffect(() => {
    const testConnections = async () => {
      const apiBase = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '/api' : 'https://hackathon-logsentinel.onrender.com/api')
      
      console.log('Environment mode:', import.meta.env.MODE)
      console.log('Environment DEV:', import.meta.env.DEV)
      console.log('Environment VITE_API_URL:', import.meta.env.VITE_API_URL)
      console.log('Final API base:', apiBase)
      
      try {
        // Test backend connection
        console.log('Testing backend connection to:', apiBase)
        const response = await axios.get(`${apiBase.replace('/api', '')}/health`, {
          timeout: 10000
        })
        
        if (response.data.status === 'ok') {
          setStatus(prev => ({ ...prev, backend: 'connected' }))
          
          // Test database connection through backend
          try {
            await axios.get(`${apiBase}/files`)
            setStatus(prev => ({ ...prev, database: 'connected' }))
          } catch (dbError) {
            console.error('Database test failed:', dbError)
            setStatus(prev => ({ 
              ...prev, 
              database: 'failed',
              error: `Database: ${dbError instanceof Error ? dbError.message : 'Unknown error'}`
            }))
          }
        } else {
          setStatus(prev => ({ 
            ...prev, 
            backend: 'failed', 
            error: `Backend returned: ${JSON.stringify(response.data)}` 
          }))
        }
      } catch (error) {
        console.error('Backend connection failed:', error)
        setStatus(prev => ({ 
          ...prev, 
          backend: 'failed', 
          database: 'failed',
          error: `Backend: ${error instanceof Error ? error.message : 'Unknown error'}`
        }))
      }
    }

    testConnections()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600'
      case 'failed': return 'text-red-600'
      default: return 'text-yellow-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return '✅'
      case 'failed': return '❌'
      default: return '🔄'
    }
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow-md mb-4">
      <h3 className="text-lg font-semibold mb-3">🔗 Connection Status</h3>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-medium">API URL:</span>
          <code className="bg-gray-100 px-2 py-1 rounded text-sm">{status.apiUrl}</code>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="font-medium">Backend:</span>
          <span className={`flex items-center gap-2 ${getStatusColor(status.backend)}`}>
            {getStatusIcon(status.backend)} {status.backend}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="font-medium">Database:</span>
          <span className={`flex items-center gap-2 ${getStatusColor(status.database)}`}>
            {getStatusIcon(status.database)} {status.database}
          </span>
        </div>
        
        {status.error && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
            <p className="text-red-700 text-sm">
              <strong>Error:</strong> {status.error}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ConnectionTest