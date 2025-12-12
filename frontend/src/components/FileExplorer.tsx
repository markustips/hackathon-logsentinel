import { useState, useEffect } from 'react'
import { Upload, File, CheckCircle, XCircle, Clock, Trash2 } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { LogFile } from '../types'

interface FileExplorerProps {
  onFileSelect: (fileId: string) => void
  selectedFileId: string | null
}

export default function FileExplorer({ onFileSelect, selectedFileId }: FileExplorerProps) {
  const [files, setFiles] = useState<LogFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const api = useApi()

  useEffect(() => {
    loadFiles()
  }, [])

  const loadFiles = async () => {
    try {
      const data = await api.listFiles()
      setFiles(data)
    } catch (error) {
      console.error('Error loading files:', error)
    }
  }

  const processFile = async (file: File) => {
    setUploading(true)
    setUploadProgress(`Uploading ${file.name}...`)

    try {
      const result = await api.uploadFile(file)
      setUploadProgress('Processing and indexing...')

      setTimeout(async () => {
        await loadFiles()
        setUploadProgress('Upload complete!')
        onFileSelect(result.file_id)

        setTimeout(() => {
          setUploadProgress('')
          setUploading(false)
        }, 2000)
      }, 1000)
    } catch (error) {
      console.error('Upload error:', error)
      setUploadProgress('Upload failed')
      setUploading(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    await processFile(file)
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const file = e.dataTransfer.files?.[0]
    if (!file) return

    // Validate file type
    const validExtensions = ['.csv', '.json', '.jsonl', '.log', '.txt']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()

    if (!validExtensions.includes(fileExtension)) {
      setUploadProgress('Invalid file type. Please upload CSV, JSON, JSONL, LOG, or TXT files.')
      setTimeout(() => setUploadProgress(''), 3000)
      return
    }

    await processFile(file)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'indexed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500 animate-spin" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <File className="w-4 h-4 text-gray-500" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString()
  }

  const handleDeleteFile = async (fileId: string) => {
    setDeleteConfirm(fileId)
  }

  const confirmDelete = async () => {
    if (!deleteConfirm) return

    setDeleting(true)
    try {
      await api.deleteFile(deleteConfirm)

      // If deleted file was selected, clear selection
      if (selectedFileId === deleteConfirm) {
        onFileSelect('')
      }

      // Reload file list
      await loadFiles()
      setUploadProgress('File deleted successfully')
      setTimeout(() => setUploadProgress(''), 2000)
    } catch (error) {
      console.error('Delete error:', error)
      setUploadProgress('Failed to delete file')
      setTimeout(() => setUploadProgress(''), 3000)
    } finally {
      setDeleting(false)
      setDeleteConfirm(null)
    }
  }

  const cancelDelete = () => {
    setDeleteConfirm(null)
  }

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Files</h2>
        <label className="cursor-pointer">
          <input
            type="file"
            accept=".csv,.json,.jsonl,.log,.txt"
            onChange={handleFileUpload}
            disabled={uploading}
            className="hidden"
          />
          <div className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors">
            <Upload className="w-4 h-4" />
            <span>Upload</span>
          </div>
        </label>
      </div>

      {/* Upload Progress */}
      {uploadProgress && (
        <div className="mb-4 p-3 bg-blue-900/30 border border-blue-700 rounded">
          <p className="text-sm text-blue-300">{uploadProgress}</p>
        </div>
      )}

      {/* File List with Drag & Drop */}
      <div
        className={`flex-1 overflow-y-auto space-y-2 rounded-lg border-2 border-dashed transition-all ${
          isDragging
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-transparent'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {files.length === 0 ? (
          <div className={`text-center py-12 transition-colors ${
            isDragging ? 'text-blue-400' : 'text-gray-400'
          }`}>
            <Upload className={`w-12 h-12 mx-auto mb-3 transition-all ${
              isDragging ? 'scale-110 opacity-100' : 'opacity-50'
            }`} />
            <p className="text-sm font-medium">
              {isDragging ? 'Drop your log file here' : 'Drag & drop logs here'}
            </p>
            <p className="text-xs mt-2 opacity-75">
              or click Upload button above
            </p>
            <p className="text-xs mt-1 opacity-50">
              Supports CSV, JSON, JSONL, LOG, TXT
            </p>
          </div>
        ) : (
          <>
            {isDragging && (
              <div className="absolute inset-0 bg-blue-500/20 rounded-lg flex items-center justify-center z-10 pointer-events-none">
                <div className="bg-gray-800 border-2 border-blue-500 rounded-lg p-6 text-center">
                  <Upload className="w-12 h-12 mx-auto mb-3 text-blue-400" />
                  <p className="text-sm font-medium text-blue-400">Drop to upload</p>
                </div>
              </div>
            )}
            {files.map((file) => (
              <div
                key={file.id}
                className={`relative group rounded border transition-all ${
                  selectedFileId === file.id
                    ? 'bg-blue-600/20 border-blue-500'
                    : 'bg-gray-800 border-gray-700 hover:bg-gray-750 hover:border-gray-600'
                }`}
              >
                <button
                  onClick={() => onFileSelect(file.id)}
                  className="w-full text-left p-3"
                >
                  <div className="flex items-start gap-2">
                    {getStatusIcon(file.status)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {file.filename}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {formatFileSize(file.file_size)} • {file.total_records} records
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatDate(file.upload_time)}
                      </p>
                    </div>
                  </div>
                </button>

                {/* Delete button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDeleteFile(file.id)
                  }}
                  className="absolute top-2 right-2 p-1.5 bg-red-600/10 hover:bg-red-600 text-red-400 hover:text-white rounded opacity-0 group-hover:opacity-100 transition-all"
                  title="Delete file"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-white mb-2">Delete File?</h3>
            <p className="text-gray-300 text-sm mb-4">
              Are you sure you want to delete this file? This will permanently remove the file and all associated log records, anomalies, and indexes.
            </p>
            <p className="text-gray-400 text-xs mb-6 font-mono">
              {files.find(f => f.id === deleteConfirm)?.filename}
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={cancelDelete}
                disabled={deleting}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {deleting ? (
                  <>
                    <Clock className="w-4 h-4 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    <span>Delete</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
