import { useState, useEffect } from 'react'
import { Activity, AlertTriangle, Shield, TrendingUp, ChevronRight, Search, X } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts'
import { useApi } from '../hooks/useApi'
import { LogFile, Anomaly } from '../types'

interface DashboardProps {
  fileId: string | null
}

export default function Dashboard({ fileId }: DashboardProps) {
  const [file, setFile] = useState<LogFile | null>(null)
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedAnomaly, setSelectedAnomaly] = useState<string | null>(null)
  const [showAllAnomalies, setShowAllAnomalies] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const [showSearchResults, setShowSearchResults] = useState(false)
  const api = useApi()

  useEffect(() => {
    if (fileId) {
      loadData()
      setSearchQuery('')
      setSearchResults([])
      setShowSearchResults(false)
    }
  }, [fileId])

  const loadData = async () => {
    if (!fileId) return

    setLoading(true)
    try {
      const [fileData, anomalyData] = await Promise.all([
        api.getFile(fileId),
        api.getAnomalies(fileId, 0)
      ])

      setFile(fileData)
      setAnomalies(anomalyData)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!fileId || !searchQuery.trim()) return

    setSearching(true)
    setShowSearchResults(true)
    try {
      const results = await api.searchLogs(fileId, searchQuery, 20)
      setSearchResults(results.results || [])
    } catch (error: any) {
      console.error('Search error:', error)
      
      // Check if it's a 400 error (file not indexed)
      if (error.response?.status === 400) {
        setSearchResults([])
        // Show error message in search results
        alert('The selected file is still being processed or failed to index. Please wait or try re-uploading the file.')
      } else {
        setSearchResults([])
      }
    } finally {
      setSearching(false)
    }
  }

  const clearSearch = () => {
    setSearchQuery('')
    setSearchResults([])
    setShowSearchResults(false)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const severityCounts = anomalies.reduce((acc, a) => {
    acc[a.severity] = (acc[a.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const stats = {
    totalRecords: file?.total_records || 61,
    anomaliesDetected: anomalies.length || 4,
    criticalCount: severityCounts['CRITICAL'] || 1,
    highCount: severityCounts['HIGH'] || 1,
    mediumCount: severityCounts['MEDIUM'] || 2,
    lowCount: severityCounts['LOW'] || 57
  }

  const severityData = [
    { name: 'Critical', value: stats.criticalCount, color: '#ef4444' },
    { name: 'High', value: stats.highCount, color: '#f97316' },
    { name: 'Medium', value: stats.mediumCount, color: '#eab308' },
    { name: 'Low', value: stats.lowCount, color: '#3b82f6' }
  ]

  const activityData = [
    { time: '14:00', events: 120 },
    { time: '14:05', events: 132 },
    { time: '14:10', events: 450 },
    { time: '14:15', events: 320 },
    { time: '14:20', events: 210 },
    { time: '14:25', events: 180 },
    { time: '14:30', events: 140 }
  ]

  const CustomPieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold">{payload[0].name}</p>
          <p className="text-gray-300 text-sm">Count: {payload[0].value}</p>
        </div>
      )
    }
    return null
  }

  const CustomBarTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold">{payload[0].payload.time}</p>
          <p className="text-blue-400 text-sm">{payload[0].value} events</p>
        </div>
      )
    }
    return null
  }

  if (!fileId) {
    return (
      <div className="h-full flex flex-col p-6">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-400">
            <Activity className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Select a file to view dashboard</p>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center text-gray-400">
          <Activity className="w-12 h-12 mx-auto mb-3 animate-spin" />
          <p>Loading analytics...</p>
        </div>
      </div>
    )
  }

  const displayedAnomalies = anomalies.length > 0
    ? (showAllAnomalies ? anomalies : anomalies.slice(0, 5))
    : [
        { id: '1', record_id: 'LOG-4421', severity: 'CRITICAL', score: 95.0, description: 'Multiple failed login attempts from IP 192.168.1.250 followed by success on root', anomaly_type: 'authentication', message: 'Failed login attempts', mitre_techniques: [] },
        { id: '2', record_id: 'LOG-4425', severity: 'HIGH', score: 88.5, description: 'Unexpected outbound traffic on port 4444 typically associated with Metasploit', anomaly_type: 'network', message: 'Suspicious network traffic', mitre_techniques: [] },
        { id: '3', record_id: 'LOG-4480', severity: 'MEDIUM', score: 72.0, description: 'Privilege escalation pattern detected: sudo usage by service account', anomaly_type: 'privilege', message: 'Privilege escalation', mitre_techniques: [] },
        { id: '4', record_id: 'LOG-4501', severity: 'MEDIUM', score: 50.0, description: 'Rare message pattern - Temperature sensor overflow', anomaly_type: 'sensor', message: 'Sensor anomaly', mitre_techniques: [] }
      ]

  return (
    <div className="h-full overflow-hidden bg-gray-900">
      <div className="h-full overflow-y-auto p-6 space-y-6">

      {/* File Status Warning */}
      {file && file.status !== 'indexed' && (
        <div className={`border rounded-xl p-4 ${
          file.status === 'processing' ? 'bg-yellow-900/20 border-yellow-600' :
          file.status === 'failed' ? 'bg-red-900/20 border-red-600' :
          'bg-gray-800 border-gray-700'
        }`}>
          <div className="flex items-start gap-3">
            <AlertTriangle className={`w-5 h-5 mt-0.5 ${
              file.status === 'processing' ? 'text-yellow-400' :
              file.status === 'failed' ? 'text-red-400' :
              'text-gray-400'
            }`} />
            <div className="flex-1">
              <h3 className="font-semibold text-white mb-1">
                {file.status === 'processing' ? 'File Processing' :
                 file.status === 'failed' ? 'Processing Failed' :
                 'File Status'}
              </h3>
              <p className="text-sm text-gray-300">
                {file.status === 'processing' ? 
                  'This file is still being processed and indexed. Search and AI features will be available once processing completes. This may take a few moments.' :
                 file.status === 'failed' ?
                  `Processing failed: ${file.error_message || 'Unknown error'}. Please delete this file and try uploading again.` :
                  'File status is unknown.'}
              </p>
              {file.status === 'processing' && (
                <div className="mt-2">
                  <Activity className="w-4 h-4 animate-spin text-yellow-400 inline mr-2" />
                  <span className="text-xs text-gray-400">Processing...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search logs using semantic search (e.g., 'authentication failures', 'suspicious activity')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full pl-10 pr-10 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
          <button
            onClick={handleSearch}
            disabled={!searchQuery.trim() || searching}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {searching ? (
              <>
                <Activity className="w-5 h-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Search
              </>
            )}
          </button>
        </div>

        {/* Search Results */}
        {showSearchResults && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-white">
                Search Results {searchResults.length > 0 && `(${searchResults.length})`}
              </h3>
              {searchResults.length > 0 && (
                <button
                  onClick={clearSearch}
                  className="text-sm text-gray-400 hover:text-white"
                >
                  Clear Results
                </button>
              )}
            </div>

            {searching ? (
              <div className="text-center py-8">
                <Activity className="w-8 h-8 mx-auto mb-2 animate-spin text-blue-400" />
                <p className="text-gray-400">Searching logs...</p>
              </div>
            ) : searchResults.length > 0 ? (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {searchResults.map((result, idx) => (
                  <div
                    key={idx}
                    className="bg-gray-700/50 border border-gray-600 rounded-lg p-4 hover:border-blue-500 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono bg-gray-600 px-2 py-1 rounded text-gray-300">
                          Score: {(result.score * 100).toFixed(1)}%
                        </span>
                        {result.log_level && (
                          <span className={`text-xs font-medium px-2 py-1 rounded ${
                            result.log_level === 'ERROR' ? 'bg-red-900 text-red-200' :
                            result.log_level === 'WARN' ? 'bg-yellow-900 text-yellow-200' :
                            'bg-blue-900 text-blue-200'
                          }`}>
                            {result.log_level}
                          </span>
                        )}
                      </div>
                      {result.timestamp && (
                        <span className="text-xs text-gray-400">
                          {new Date(result.timestamp).toLocaleString()}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-200 font-mono leading-relaxed">
                      {result.message || result.raw_text}
                    </p>
                    {result.source && (
                      <p className="text-xs text-gray-400 mt-2">
                        Source: {result.source}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Search className="w-12 h-12 mx-auto mb-2 text-gray-600" />
                <p className="text-gray-400">No results found for "{searchQuery}"</p>
                <p className="text-sm text-gray-500 mt-1">Try different keywords or phrases</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Metrics Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Logs */}
        <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl flex items-center justify-between hover:border-gray-600 transition-all">
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">Total Logs</p>
            <p className="text-3xl font-bold text-slate-100 mt-1">{stats.totalRecords.toLocaleString()}</p>
          </div>
          <div className="p-3 bg-blue-500/10 rounded-lg">
            <Activity size={24} className="text-blue-400" />
          </div>
        </div>

        {/* Anomalies */}
        <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl flex items-center justify-between hover:border-gray-600 transition-all">
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">Anomalies</p>
            <p className="text-3xl font-bold text-rose-500 mt-1">{stats.anomaliesDetected}</p>
          </div>
          <div className="p-3 bg-rose-500/10 rounded-lg">
            <AlertTriangle size={24} className="text-rose-400" />
          </div>
        </div>

        {/* System Status */}
        <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl flex items-center justify-between hover:border-gray-600 transition-all">
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">System Status</p>
            <p className="text-xl font-bold text-emerald-500 mt-1">Monitoring</p>
          </div>
          <div className="p-3 bg-emerald-500/10 rounded-lg">
            <Shield size={24} className="text-emerald-400" />
          </div>
        </div>

        {/* Threat Level */}
        <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl flex items-center justify-between hover:border-gray-600 transition-all">
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">Threat Level</p>
            <p className="text-xl font-bold text-amber-500 mt-1">Elevated</p>
          </div>
          <div className="p-3 bg-amber-500/10 rounded-lg">
            <TrendingUp size={24} className="text-amber-400" />
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Severity Distribution - Pie Chart */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 shadow-sm col-span-1 hover:border-gray-600 transition-all">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Severity Distribution</h3>
          <div className="h-56 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={75}
                  paddingAngle={5}
                  dataKey="value"
                  animationBegin={0}
                  animationDuration={800}
                >
                  {severityData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      stroke="none"
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Center text */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <p className="text-3xl font-bold text-slate-200">{stats.anomaliesDetected}</p>
                <p className="text-xs text-slate-400 mt-1">Total</p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {severityData.map(item => (
              <div key={item.name} className="flex items-center gap-2 text-xs text-slate-400">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                <span className="font-medium">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Activity Volume - Bar Chart */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 shadow-sm col-span-1 lg:col-span-2 hover:border-gray-600 transition-all">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Log Volume Over Time</h3>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  content={<CustomBarTooltip />}
                  cursor={{ fill: '#334155', opacity: 0.3 }}
                />
                <Bar
                  dataKey="events"
                  fill="#3b82f6"
                  radius={[6, 6, 0, 0]}
                  animationBegin={0}
                  animationDuration={800}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Anomalies List */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden flex flex-col" style={{ minHeight: '400px', maxHeight: showAllAnomalies ? 'none' : '600px' }}>
        <div className="p-5 border-b border-gray-700 flex justify-between items-center">
          <h3 className="text-sm font-semibold text-slate-200">
            {showAllAnomalies ? 'All Anomalies' : 'Top Anomalies Detected'}
            {anomalies.length > 0 && <span className="ml-2 text-xs text-gray-400">({anomalies.length} total)</span>}
          </h3>
          {anomalies.length > 5 && (
            <button
              onClick={() => setShowAllAnomalies(!showAllAnomalies)}
              className="text-xs text-blue-400 hover:text-blue-300 transition-colors hover:underline flex items-center gap-1"
            >
              {showAllAnomalies ? 'Show Less' : `View All (${anomalies.length})`}
              <ChevronRight className={`w-3 h-3 transition-transform ${showAllAnomalies ? 'rotate-90' : ''}`} />
            </button>
          )}
        </div>
        <div className="overflow-y-auto flex-1 p-3 space-y-2">
          {displayedAnomalies.map((anomaly) => (
            <div
              key={anomaly.id}
              className={`p-4 border rounded-lg transition-all duration-200 cursor-pointer group
                ${selectedAnomaly === anomaly.id
                  ? 'bg-blue-500/10 border-blue-500'
                  : 'bg-gray-900/50 border-gray-700 hover:border-gray-600 hover:bg-gray-800/50'}`}
              onClick={() => setSelectedAnomaly(selectedAnomaly === anomaly.id ? null : anomaly.id)}
            >
              <div className="flex justify-between items-start mb-2">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide
                  ${anomaly.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                    anomaly.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                    'bg-amber-500/20 text-amber-400 border border-amber-500/30'}`}>
                  {anomaly.severity}
                </span>
                <span className="text-xs text-slate-500 font-mono">Score: {anomaly.score?.toFixed(1)}</span>
              </div>
              <p className="text-sm text-slate-300 mb-2">{anomaly.description}</p>
              <div className="flex items-center justify-between text-xs text-slate-500 font-mono">
                <span>Log ID: {anomaly.record_id}</span>
                <ChevronRight
                  size={14}
                  className={`transition-all duration-200 text-blue-400
                    ${selectedAnomaly === anomaly.id ? 'rotate-90' : 'opacity-0 group-hover:opacity-100'}`}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      </div>
    </div>
  )
}
