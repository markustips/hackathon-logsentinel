import axios from 'axios'
import { LogFile, Anomaly, CopilotMessage } from '../types'

// Use environment variable for API URL in production, fallback to local for development
const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '/api' : 'https://hackathon-logsentinel.onrender.com/api')

// Debug logging to verify environment variable
console.log('Environment mode:', import.meta.env.MODE)
console.log('Environment DEV:', import.meta.env.DEV)
console.log('Environment VITE_API_URL:', import.meta.env.VITE_API_URL)
console.log('Final API Base URL:', API_BASE)

export const useApi = () => {
  // Upload file
  const uploadFile = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(`${API_BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  // List files
  const listFiles = async (): Promise<LogFile[]> => {
    const response = await axios.get(`${API_BASE}/files`)
    return response.data.files
  }

  // Get file details
  const getFile = async (fileId: string): Promise<LogFile> => {
    const response = await axios.get(`${API_BASE}/files/${fileId}`)
    return response.data
  }

  // Search logs
  const searchLogs = async (fileId: string, query: string, k: number = 10) => {
    const response = await axios.post(`${API_BASE}/search`, {
      file_id: fileId,
      query,
      k
    })
    return response.data
  }

  // Detect anomalies
  const detectAnomalies = async (fileId: string) => {
    const response = await axios.post(`${API_BASE}/detect-anomalies/${fileId}`)
    return response.data
  }

  // Get anomalies
  const getAnomalies = async (fileId: string, minScore: number = 0): Promise<Anomaly[]> => {
    const response = await axios.get(`${API_BASE}/anomalies`, {
      params: { file_id: fileId, min_score: minScore, limit: 100 }
    })
    return response.data
  }

  // Get timeline
  const getTimeline = async (fileId: string) => {
    const response = await axios.get(`${API_BASE}/timeline/${fileId}`)
    return response.data
  }

  // Chat with copilot
  const chatWithCopilot = async (
    fileId: string,
    message: string,
    history: CopilotMessage[]
  ) => {
    const response = await axios.post(`${API_BASE}/copilot/chat`, {
      file_id: fileId,
      message,
      history
    })
    return response.data
  }

  // Chat with copilot using streaming
  const chatWithCopilotStream = async (
    fileId: string,
    message: string,
    history: CopilotMessage[],
    onProgress: (event: any) => void,
    onComplete: (result: any) => void,
    onError: (error: any) => void
  ) => {
    try {
      const response = await fetch(`${API_BASE}/copilot/chat-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_id: fileId,
          message,
          history
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No reader available')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process complete lines
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim() === '') continue
          if (!line.startsWith('data: ')) continue

          try {
            const data = JSON.parse(line.substring(6))

            if (data.type === 'status') {
              onProgress(data)
            } else if (data.type === 'result') {
              onComplete(data)
            } else if (data.type === 'error') {
              onError(new Error(data.message))
            }
          } catch (parseError) {
            console.error('Error parsing SSE data:', parseError)
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error)
      onError(error)
    }
  }

  // Delete file
  const deleteFile = async (fileId: string) => {
    const response = await axios.delete(`${API_BASE}/files/${fileId}`)
    return response.data
  }

  return {
    uploadFile,
    listFiles,
    getFile,
    deleteFile,
    searchLogs,
    detectAnomalies,
    getAnomalies,
    getTimeline,
    chatWithCopilot,
    chatWithCopilotStream
  }
}
